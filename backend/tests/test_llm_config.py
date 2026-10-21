import os
import unittest
from unittest.mock import patch, MagicMock
from backend.app.core.llm_config import (
    build_node_configs,
    get_node_config,
    validate_node_temperature,
    refresh_node_configs,
    NodeLLMConfig,
    DEFAULT_NODE_SPECS,
)
from backend.app.core.llm_factory import (
    get_node_llm,
    model_supports_temperature,
    _create_cached_llm,
)


class TestLLMConfigAndFactory(unittest.TestCase):

    def test_default_node_temperatures_and_tokens(self):
        """Verify each node receives the expected baseline temperature and tokens."""
        with patch.dict(os.environ, {}, clear=True):
            configs = build_node_configs()

            self.assertEqual(configs["verifier_agent"].temperature, 0.0)
            self.assertEqual(configs["verifier_agent"].max_tokens, 1500)

            self.assertEqual(configs["research_agent"].temperature, 0.0)
            self.assertEqual(configs["research_agent"].max_tokens, 512)

            self.assertEqual(configs["plan_queries"].temperature, 0.0)
            self.assertEqual(configs["plan_queries"].max_tokens, 512)

            self.assertEqual(configs["extract_facts"].temperature, 0.0)
            self.assertEqual(configs["extract_facts"].max_tokens, 2048)

            self.assertEqual(configs["translator"].temperature, 0.2)
            self.assertEqual(configs["translator"].max_tokens, 4096)

            self.assertEqual(configs["content_generator"].temperature, 0.35)
            self.assertEqual(configs["content_generator"].max_tokens, 4096)

            self.assertEqual(configs["title_generator"].temperature, 0.5)
            self.assertEqual(configs["title_generator"].max_tokens, 150)

    def test_node_aliases(self):
        """Verify common aliases map correctly to canonical node names."""
        self.assertEqual(get_node_config("writer").node_name, "content_generator")
        self.assertEqual(get_node_config("reviewer").node_name, "verifier_agent")
        self.assertEqual(get_node_config("verifier").node_name, "verifier_agent")
        self.assertEqual(get_node_config("title").node_name, "title_generator")
        self.assertEqual(get_node_config("research").node_name, "research_agent")
        self.assertEqual(get_node_config("translate").node_name, "translator")

    def test_environment_variable_overrides(self):
        """Verify that per-node environment variables successfully override defaults."""
        env_overrides = {
            "WRITER_TEMPERATURE": "0.35",
            "WRITER_MAX_TOKENS": "3500",
            "VERIFIER_TEMPERATURE": "0.0",
            "TITLE_TEMPERATURE": "0.7",
        }
        with patch.dict(os.environ, env_overrides, clear=True):
            configs = build_node_configs()

            self.assertEqual(configs["content_generator"].temperature, 0.35)
            self.assertEqual(configs["content_generator"].max_tokens, 3500)
            self.assertEqual(configs["content_generator"].source, "env")

            self.assertEqual(configs["title_generator"].temperature, 0.7)
            self.assertEqual(configs["title_generator"].source, "env")

    def test_invalid_temperature_rejected(self):
        """Verify startup validation raises clear error on negative or out-of-range temperatures."""
        with self.assertRaises(ValueError):
            validate_node_temperature("verifier_agent", temp=-0.1, provider="groq")

        with self.assertRaises(ValueError):
            validate_node_temperature("content_generator", temp=2.5, provider="openai")

        with self.assertRaises(ValueError):
            validate_node_temperature("content_generator", temp=1.2, provider="anthropic")

    def test_reasoning_model_detection(self):
        """Verify that reasoning models are correctly identified and do not accept temperature."""
        self.assertTrue(model_supports_temperature("openai/gpt-oss-120b"))
        self.assertTrue(model_supports_temperature("llama-3.3-70b-versatile"))
        self.assertTrue(model_supports_temperature("gpt-4o"))

        # Reasoning models must return False
        self.assertFalse(model_supports_temperature("o1"))
        self.assertFalse(model_supports_temperature("o1-mini"))
        self.assertFalse(model_supports_temperature("o1-preview"))
        self.assertFalse(model_supports_temperature("o3-mini"))
        self.assertFalse(model_supports_temperature("openai/o1-mini"))

    def test_reasoning_model_omits_temperature_gracefully(self):
        """Verify that when a reasoning model is configured, get_node_llm does not crash."""
        with patch("backend.app.core.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value.MODEL_PROVIDER = "openai"
            mock_settings.return_value.OPENAI_API_KEY = "test_key"
            mock_settings.return_value.LANGSMITH_TRACING = False

            with patch("backend.app.core.llm_factory.get_node_config") as mock_cfg:
                mock_cfg.return_value = NodeLLMConfig(
                    node_name="content_generator",
                    model="o1-mini",
                    temperature=0.4,
                    max_tokens=2048,
                )

                with patch("backend.app.core.llm_factory._create_cached_llm") as mock_create:
                    mock_create.return_value = MagicMock()
                    llm = get_node_llm("content_generator")

                    # The passed temperature must be None because o1-mini is a reasoning model
                    _, kwargs = mock_create.call_args
                    self.assertIsNone(kwargs["temperature"])
                    self.assertEqual(kwargs["model"], "o1-mini")

    def test_creativity_offset_applied_only_to_writing(self):
        """Verify that creativity level adjusts writing nodes but leaves verifier locked at 0.0."""
        with patch("backend.app.core.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value.MODEL_PROVIDER = "groq"
            mock_settings.return_value.GROQ_API_KEY = "test_key"
            mock_settings.return_value.LANGSMITH_TRACING = False

            with patch("backend.app.core.llm_factory._create_cached_llm") as mock_create:
                mock_create.return_value = MagicMock()

                # 1. Writing node with 'low' creativity -> 0.35 - 0.1 = 0.25
                get_node_llm("content_generator", creativity_level="low")
                _, kwargs = mock_create.call_args
                self.assertEqual(kwargs["temperature"], 0.25)

                # 2. Writing node with 'high' creativity -> 0.35 + 0.1 = 0.45
                get_node_llm("content_generator", creativity_level="high")
                _, kwargs = mock_create.call_args
                self.assertEqual(kwargs["temperature"], 0.45)

                # 3. Verifier node with 'high' creativity -> MUST REMAIN 0.0
                get_node_llm("verifier_agent", creativity_level="high")
                _, kwargs = mock_create.call_args
                self.assertEqual(kwargs["temperature"], 0.0)

    def test_verifier_loop_temperature_step_down(self):
        """Simulate verifier retry loop to verify temperature steps down by 0.1 per revision."""
        writer_cfg = get_node_config("content_generator")
        base_temp = writer_cfg.temperature  # 0.35

        # Revision 0 (Initial draft)
        rev0_temp = max(0.1, round(base_temp - (0.1 * 0), 2))
        self.assertEqual(rev0_temp, 0.35)

        # Revision 1 (After 1st rejection)
        rev1_temp = max(0.1, round(base_temp - (0.1 * 1), 2))
        self.assertEqual(rev1_temp, 0.25)

        # Revision 2 (After 2nd rejection)
        rev2_temp = max(0.1, round(base_temp - (0.1 * 2), 2))
        self.assertEqual(rev2_temp, 0.15)

        # Lower bound test (never drop below 0.1)
        rev5_temp = max(0.1, round(base_temp - (0.1 * 5), 2))
        self.assertEqual(rev5_temp, 0.1)


if __name__ == "__main__":
    unittest.main()
