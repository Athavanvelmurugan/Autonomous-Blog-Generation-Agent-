import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { generateBlogStream } from '../services/api';
import { useToast } from './ToastContext';

const GenerationContext = createContext(null);

export function GenerationProvider({ children }) {
  const { addToast } = useToast();

  // Active form inputs
  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState('Informative');
  const [targetLanguage, setTargetLanguage] = useState('English');

  // Execution state
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [stepsCompleted, setStepsCompleted] = useState([]);
  const [liveTelemetry, setLiveTelemetry] = useState(null);
  const [revisionCount, setRevisionCount] = useState(0);
  const [activeResult, setActiveResult] = useState(null);
  const [generationError, setGenerationError] = useState(null);
  const [executionLogs, setExecutionLogs] = useState([]);

  // Ref to cancel/abort if needed
  const isGeneratingRef = useRef(false);

  const startGeneration = useCallback(async (payload, onCompleteNavigate) => {
    const { topic: t, tone: to, target_language: tl } = payload;
    if (!t || !t.trim()) return;

    setIsGenerating(true);
    isGeneratingRef.current = true;
    setGenerationError(null);
    setCurrentStep('plan_queries');
    setStepsCompleted([]);
    setLiveTelemetry('Initializing LangGraph Multi-Agent execution pipeline...');
    setRevisionCount(0);
    setActiveResult(null);

    const initialLog = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      node: 'system',
      message: `Launched autonomous pipeline for: "${t.slice(0, 50)}..." [Tone: ${to}, Language: ${tl}]`,
    };
    setExecutionLogs([initialLog]);

    try {
      await generateBlogStream(
        { topic: t, tone: to, target_language: tl },
        (event) => {
          if (!isGeneratingRef.current) return;

          const now = new Date().toLocaleTimeString();

          if (event.type === 'step_start') {
            setCurrentStep(event.node);
            if (event.message) {
              setLiveTelemetry(event.message);
              setExecutionLogs((prev) => [
                ...prev,
                { id: Date.now() + Math.random(), timestamp: now, node: event.node, message: event.message },
              ]);
            }
          } else if (event.type === 'node_update') {
            setCurrentStep(event.node);
            if (event.revision_count !== undefined) {
              setRevisionCount(event.revision_count);
            }
            if (event.message) {
              setLiveTelemetry(event.message);
              setExecutionLogs((prev) => [
                ...prev,
                { id: Date.now() + Math.random(), timestamp: now, node: event.node, message: event.message, data: event },
              ]);
            }
            if (event.steps_completed && event.steps_completed.length > 0) {
              setStepsCompleted(event.steps_completed);
            } else {
              setStepsCompleted((prev) => Array.from(new Set([...prev, event.node])));
            }
          } else if (event.type === 'complete') {
            const finalBlog = event.blog;
            const finalSteps = finalBlog.steps_completed || [
              'plan_queries',
              'collect',
              'clean_dedupe',
              'extract_facts',
              'title_generator',
              'content_generator',
              'verifier_agent',
            ];
            if (tl.toLowerCase() !== 'english') {
              finalSteps.push('translator');
            }
            finalSteps.push('storage');

            setStepsCompleted(Array.from(new Set(finalSteps)));
            setCurrentStep('');
            setActiveResult(finalBlog);
            setLiveTelemetry(null);
            setIsGenerating(false);
            isGeneratingRef.current = false;

            setExecutionLogs((prev) => [
              ...prev,
              {
                id: Date.now(),
                timestamp: now,
                node: 'storage',
                message: `Pipeline finished! Verified article saved to PostgreSQL (ID #${finalBlog.id}) in ${finalBlog.execution_time_seconds}s.`,
              },
            ]);

            addToast(`Article generated successfully! Fact Check: ${finalBlog.verification_score || 8.5}/10`, 'success');

            if (onCompleteNavigate) {
              onCompleteNavigate(finalBlog);
            }
          } else if (event.type === 'error') {
            const errDetail = event.detail || event.message || 'Pipeline execution error';
            setGenerationError(errDetail);
            setIsGenerating(false);
            isGeneratingRef.current = false;
            setCurrentStep('');
            setLiveTelemetry(null);
            addToast(`Generation failed: ${errDetail}`, 'error');
          }
        },
        (err) => {
          const msg = err.response?.data?.detail || err.message || 'Error occurred during generation';
          setGenerationError(msg);
          setIsGenerating(false);
          isGeneratingRef.current = false;
          setCurrentStep('');
          setLiveTelemetry(null);
          addToast(`Generation error: ${msg}`, 'error');
        }
      );
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Error occurred during generation';
      setGenerationError(msg);
      setIsGenerating(false);
      isGeneratingRef.current = false;
      setCurrentStep('');
      setLiveTelemetry(null);
      addToast(`Generation error: ${msg}`, 'error');
    }
  }, [addToast]);

  const cancelGeneration = useCallback(() => {
    isGeneratingRef.current = false;
    setIsGenerating(false);
    setCurrentStep('');
    setLiveTelemetry(null);
    addToast('Generation stopped', 'warning');
  }, [addToast]);

  return (
    <GenerationContext.Provider
      value={{
        topic,
        setTopic,
        tone,
        setTone,
        targetLanguage,
        setTargetLanguage,
        isGenerating,
        currentStep,
        stepsCompleted,
        liveTelemetry,
        revisionCount,
        activeResult,
        setActiveResult,
        generationError,
        executionLogs,
        startGeneration,
        cancelGeneration,
      }}
    >
      {children}
    </GenerationContext.Provider>
  );
}

export function useGeneration() {
  const context = useContext(GenerationContext);
  if (!context) {
    throw new Error('useGeneration must be used within a GenerationProvider');
  }
  return context;
}
