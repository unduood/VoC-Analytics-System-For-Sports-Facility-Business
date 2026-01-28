'use client';

import { useState, useCallback, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { submitAnalysisCorrections } from '@/lib/api';
import { feedbackKeys } from './useFeedback';
import type {
  FeedbackWithAnalysis,
  SentimentLabel,
  IntentLabel,
  AspectLabel,
  AnalysisCorrectionRequest,
  AnalysisCorrectionResponse,
  IntentCorrection,
  AspectCorrection,
  PaginatedResponse,
} from '@/lib/types';

// === Original Prediction State (captured when editing starts) ===
// Stores the original system predictions (from model or rating) before any user edits.

interface OriginalPredictionState {
  sentiment: {
    value: SentimentLabel;
    // The true pre-edit source (model, rating) — NOT 'user'
    originalSource: 'model' | 'rating';
  } | null;
  // Map of intent label -> original prediction info (for detecting delete+re-add)
  intents: Map<IntentLabel, { id: string; originalSource: 'model' | 'rating' }>;
  // Map of aspect -> original prediction info (for detecting delete+re-add)
  aspects: Map<AspectLabel, { id: string; sentiment: SentimentLabel; originalSource: 'model' | 'rating' }>;
}

// === Edit State Types ===

export interface SentimentEditState {
  sentiment: SentimentLabel;
  // The original prediction value (before any user edit)
  originalSentiment: SentimentLabel;
  // Current source (computed based on whether value matches original prediction)
  source: 'model' | 'user' | 'rating';
  // The true pre-edit source to restore on revert (model or rating, never user)
  originalSource: 'model' | 'rating';
}

export interface IntentEditState {
  id: string | null; // null for new intents
  intent: IntentLabel;
  // The original prediction for this intent (before any user edit)
  originalIntent: IntentLabel | null;
  source: 'model' | 'user' | 'rating';
  // The true pre-edit source to restore on revert (never 'user')
  originalSource: 'model' | 'rating';
  isDeleted: boolean;
  isNew: boolean;
  // Track if this had an original system prediction (model or rating)
  hadOriginalPrediction: boolean;
}

export interface AspectEditState {
  id: string | null; // null for new aspects
  aspect: AspectLabel;
  sentiment: SentimentLabel;
  // The original sentiment prediction for this aspect (before any user edit)
  originalSentiment: SentimentLabel | null;
  source: 'model' | 'user' | 'rating';
  // The true pre-edit source to restore on revert (never 'user')
  originalSource: 'model' | 'rating';
  isDeleted: boolean;
  isNew: boolean;
  // Track if this had an original system prediction (model or rating)
  hadOriginalPrediction: boolean;
}

export interface AnalysisEditState {
  sentiment: SentimentEditState | null;
  intents: IntentEditState[];
  aspects: AspectEditState[];
}

// === Hook Return Type ===

export interface UseAnalysisCorrectionReturn {
  isEditing: boolean;
  editState: AnalysisEditState | null;
  startEditing: (feedback: FeedbackWithAnalysis) => void;
  cancelEditing: () => void;
  saveCorrections: () => void;
  updateSentiment: (sentiment: SentimentLabel) => void;
  revertSentiment: () => void;
  updateIntent: (index: number, intent: IntentLabel) => void;
  deleteIntent: (index: number) => void;
  addIntent: (intent: IntentLabel) => void;
  revertIntent: (index: number) => void;
  updateAspect: (index: number, sentiment: SentimentLabel) => void;
  deleteAspect: (index: number) => void;
  addAspect: (aspect: AspectLabel, sentiment: SentimentLabel) => void;
  revertAspect: (index: number) => void;
  revertAllIntents: () => void;
  revertAllAspects: () => void;
  canRevertIntents: boolean;
  canRevertAspects: boolean;
  canSave: boolean;
  validationError: string | null;
  isSaving: boolean;
  error: Error | null;
}

/**
 * Hook for managing human-in-the-loop analysis corrections
 *
 * Key design principle: Compare FINAL state against ORIGINAL PREDICTIONS
 * to determine if something is truly a "user" edit, regardless of
 * the intermediate steps (delete, add, modify) taken to get there.
 */
export function useAnalysisCorrection(
  feedbackId: string
): UseAnalysisCorrectionReturn {
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [editState, setEditState] = useState<AnalysisEditState | null>(null);
  const [originalFeedback, setOriginalFeedback] = useState<FeedbackWithAnalysis | null>(null);
  const [originalPredictions, setOriginalPredictions] = useState<OriginalPredictionState | null>(null);

  // Mutation for saving corrections
  const mutation = useMutation({
    mutationFn: (corrections: AnalysisCorrectionRequest) =>
      submitAnalysisCorrections(feedbackId, corrections),

    onSuccess: (response: AnalysisCorrectionResponse) => {
      const updatedFields = {
        sentiment_result: response.sentiment,
        intent_results: response.intents,
        aspect_results: response.aspects,
        analysis_summary: response.analysis_summary,
        updated_at: response.updated_at,
      };

      // Update detail cache
      queryClient.setQueryData(
        feedbackKeys.detail(feedbackId),
        (old: FeedbackWithAnalysis | undefined) => {
          if (!old) return old;
          return { ...old, ...updatedFields };
        }
      );

      // Update list caches for immediate UI update
      queryClient.setQueriesData(
        { queryKey: feedbackKeys.lists() },
        (old: PaginatedResponse<FeedbackWithAnalysis> | undefined) => {
          if (!old?.items) return old;
          return {
            ...old,
            items: old.items.map((item) =>
              item.id === feedbackId ? { ...item, ...updatedFields } : item
            ),
          };
        }
      );

      // Invalidate dashboard
      queryClient.invalidateQueries({ queryKey: feedbackKeys.dashboard() });

      // Exit edit mode
      setIsEditing(false);
      setEditState(null);
      setOriginalFeedback(null);
      setOriginalPredictions(null);
    },
  });

  // === Start/Cancel Editing ===

  const startEditing = useCallback((feedback: FeedbackWithAnalysis) => {
    setOriginalFeedback(feedback);

    // Helper: Resolve the true pre-edit source.
    // original_source is set by the backend on first user edit.
    // If null, the current source IS the original (never been edited).
    // Fallback to 'model' for safety (e.g., legacy data).
    const resolveOriginalSource = (
      originalSource: string | null | undefined,
      currentSource: string
    ): 'model' | 'rating' => {
      const src = originalSource || currentSource;
      return src === 'rating' ? 'rating' : 'model';
    };

    // Build original prediction state map for comparison
    const predictions: OriginalPredictionState = {
      sentiment: feedback.sentiment_result
        ? {
            value: feedback.sentiment_result.original_sentiment || feedback.sentiment_result.sentiment,
            originalSource: resolveOriginalSource(
              feedback.sentiment_result.original_source,
              feedback.sentiment_result.source
            ),
          }
        : null,
      intents: new Map(),
      aspects: new Map(),
    };

    // Store original intent predictions (include deleted items so cross-session re-add detects them)
    feedback.intent_results
      .forEach((i) => {
        const originalIntentValue = i.original_intent || (i.source !== 'user' ? i.intent : null);
        const intentOriginalSource = resolveOriginalSource(i.original_source, i.source);
        if (originalIntentValue) {
          predictions.intents.set(originalIntentValue, { id: i.id, originalSource: intentOriginalSource });
        }
      });

    // Store original aspect predictions (only when a prediction exists, so user-created aspects stay out of the map)
    feedback.aspect_results
      .forEach((a) => {
        const originalSentimentValue = a.original_sentiment || (a.source !== 'user' ? a.sentiment : null);
        if (originalSentimentValue) {
          predictions.aspects.set(a.aspect, {
            id: a.id,
            sentiment: originalSentimentValue,
            originalSource: resolveOriginalSource(a.original_source, a.source),
          });
        }
      });

    setOriginalPredictions(predictions);

    // Build edit state
    setEditState({
      sentiment: feedback.sentiment_result
        ? {
            sentiment: feedback.sentiment_result.sentiment,
            originalSentiment:
              feedback.sentiment_result.original_sentiment ||
              feedback.sentiment_result.sentiment,
            source: feedback.sentiment_result.source,
            originalSource: resolveOriginalSource(
              feedback.sentiment_result.original_source,
              feedback.sentiment_result.source
            ),
          }
        : null,
      intents: feedback.intent_results
        .filter((i) => !i.is_deleted)
        .map((i) => ({
          id: i.id,
          intent: i.intent,
          originalIntent: i.original_intent || (i.source !== 'user' ? i.intent : null),
          source: i.source,
          originalSource: resolveOriginalSource(i.original_source, i.source),
          isDeleted: false,
          isNew: false,
          hadOriginalPrediction: i.source !== 'user' || !!i.original_intent,
        })),
      aspects: feedback.aspect_results
        .filter((a) => !a.is_deleted)
        .map((a) => ({
          id: a.id,
          aspect: a.aspect,
          sentiment: a.sentiment,
          originalSentiment: a.original_sentiment || (a.source !== 'user' ? a.sentiment : null),
          source: a.source,
          originalSource: resolveOriginalSource(a.original_source, a.source),
          isDeleted: false,
          isNew: false,
          hadOriginalPrediction: a.source !== 'user' || !!a.original_sentiment,
        })),
    });
    setIsEditing(true);
  }, []);

  const cancelEditing = useCallback(() => {
    setIsEditing(false);
    setEditState(null);
    setOriginalFeedback(null);
    setOriginalPredictions(null);
    mutation.reset();
  }, [mutation]);

  // === Sentiment Modifiers ===

  const updateSentiment = useCallback((sentiment: SentimentLabel) => {
    setEditState((prev) => {
      if (!prev || !prev.sentiment) return prev;

      // If value matches original prediction, restore the true original source
      const matchesPrediction = sentiment === prev.sentiment.originalSentiment;
      const newSource: 'model' | 'user' | 'rating' = matchesPrediction
        ? prev.sentiment.originalSource  // Restore original source (could be 'rating')
        : 'user';

      return {
        ...prev,
        sentiment: {
          ...prev.sentiment,
          sentiment,
          source: newSource,
        },
      };
    });
  }, []);

  const revertSentiment = useCallback(() => {
    setEditState((prev) => {
      if (!prev || !prev.sentiment) return prev;
      return {
        ...prev,
        sentiment: {
          ...prev.sentiment,
          sentiment: prev.sentiment.originalSentiment,
          // Restore the true original source (could be 'rating', not always 'model')
          source: prev.sentiment.originalSource,
        },
      };
    });
  }, []);

  // === Intent Modifiers ===

  const updateIntent = useCallback((index: number, intent: IntentLabel) => {
    setEditState((prev) => {
      if (!prev) return prev;
      let newIntents = [...prev.intents];
      const item = newIntents[index];
      if (item) {
        // Prevent duplicate: if another active intent already has this value, do nothing
        if (newIntents.some((i, idx) => idx !== index && !i.isDeleted && i.intent === intent)) {
          return prev;
        }

        // If value matches this record's own original prediction, restore its source
        const matchesOwnOriginal = item.originalIntent && intent === item.originalIntent;
        // Also check if value matches ANY original prediction (e.g., from
        // a different record that was deleted in this editing session)
        const crossPredictionInfo = !matchesOwnOriginal ? originalPredictions?.intents.get(intent) : null;

        newIntents[index] = {
          ...item,
          intent,
          source: matchesOwnOriginal
            ? item.originalSource
            : crossPredictionInfo
              ? crossPredictionInfo.originalSource
              : 'user',
        };

        // Handle off_topic mutual exclusivity
        if (intent === 'off_topic') {
          // When changing TO off_topic, auto-delete all other intents
          newIntents = newIntents.map((i, idx) => {
            if (idx !== index && !i.isDeleted) {
              if (i.isNew) {
                // Mark for removal (will be filtered later or handled)
                return { ...i, isDeleted: true };
              }
              return { ...i, isDeleted: true };
            }
            return i;
          });
          // Remove truly new items that are marked deleted
          newIntents = newIntents.filter((i) => !(i.isNew && i.isDeleted));
        }
      }
      return { ...prev, intents: newIntents };
    });
  }, [originalPredictions]);

  const deleteIntent = useCallback((index: number) => {
    setEditState((prev) => {
      if (!prev) return prev;
      const newIntents = [...prev.intents];
      if (newIntents[index]) {
        if (newIntents[index].isNew) {
          newIntents.splice(index, 1);
        } else {
          newIntents[index] = { ...newIntents[index], isDeleted: true };
        }
      }
      return { ...prev, intents: newIntents };
    });
  }, []);

  const addIntent = useCallback((intent: IntentLabel) => {
    setEditState((prev) => {
      if (!prev || !originalPredictions) return prev;

      // Prevent duplicate: if this intent is already active, do nothing
      if (prev.intents.some((i) => !i.isDeleted && i.intent === intent)) {
        return prev;
      }

      // CHECK: Is there a deleted item we should restore instead of creating new?
      // Match by actual intent value OR by original prediction value.
      const deletedItem = prev.intents.find(
        (i) => i.isDeleted && (i.intent === intent || i.originalIntent === intent)
      );

      if (deletedItem) {
        // Determine if this restores the original prediction
        const isRestoringPrediction = deletedItem.originalIntent === intent;

        return {
          ...prev,
          intents: prev.intents
            .map((i) => {
              if (i === deletedItem) {
                return {
                  ...i,
                  isDeleted: false,
                  intent,
                  // Restore original source when value matches prediction; keep existing source otherwise
                  source: isRestoringPrediction ? i.originalSource : i.source,
                };
              }
              // Mutual exclusivity: adding off_topic → delete all others
              if (intent === 'off_topic' && !i.isDeleted) {
                return { ...i, isDeleted: true };
              }
              // Mutual exclusivity: adding non-off_topic → delete off_topic
              if (i.intent === 'off_topic' && !i.isDeleted && intent !== 'off_topic') {
                return { ...i, isDeleted: true };
              }
              return i;
            })
            .filter((i) => !(i.isNew && i.isDeleted)),
        };
      }

      // Check if this intent matches an original prediction
      const originalPredictionInfo = originalPredictions.intents.get(intent);
      const hadPrediction = !!originalPredictionInfo;

      // Mutual exclusivity:
      // - Adding off_topic → delete all other non-deleted intents
      // - Adding non-off_topic → delete off_topic if present
      let updatedIntents = prev.intents.map((i) => {
        if (intent === 'off_topic' && !i.isDeleted) {
          return { ...i, isDeleted: true };
        }
        if (i.intent === 'off_topic' && !i.isDeleted && intent !== 'off_topic') {
          return { ...i, isDeleted: true };
        }
        return i;
      });
      // Remove truly new items that got marked deleted by exclusivity
      updatedIntents = updatedIntents.filter((i) => !(i.isNew && i.isDeleted));

      // Use the tracked original source if this was a known prediction
      const resolvedOriginalSource = originalPredictionInfo?.originalSource || 'model';

      return {
        ...prev,
        intents: [
          ...updatedIntents,
          {
            id: null,
            intent,
            originalIntent: hadPrediction ? intent : null,
            source: hadPrediction ? resolvedOriginalSource : 'user',
            originalSource: resolvedOriginalSource,
            isDeleted: false,
            isNew: true,
            hadOriginalPrediction: hadPrediction,
          },
        ],
      };
    });
  }, [originalPredictions]);

  const revertIntent = useCallback((index: number) => {
    setEditState((prev) => {
      if (!prev) return prev;
      const newIntents = [...prev.intents];
      const item = newIntents[index];
      if (item && item.originalIntent) {
        // Prevent duplicate: if reverting would clash with another active intent, do nothing
        if (newIntents.some((i, idx) => idx !== index && !i.isDeleted && i.intent === item.originalIntent)) {
          return prev;
        }
        newIntents[index] = {
          ...item,
          intent: item.originalIntent,
          // Restore the true original source (not hardcoded 'model')
          source: item.originalSource,
        };
      }
      return { ...prev, intents: newIntents };
    });
  }, []);

  const revertAllIntents = useCallback(() => {
    setEditState((prev) => {
      if (!prev || !originalPredictions) return prev;

      const predictionIntents = originalPredictions.intents;
      const coveredPredictionLabels = new Set<IntentLabel>();

      // Process existing edit-state items
      const newIntents = prev.intents
        .filter((item) => {
          // User-created new items (no original prediction) → remove entirely
          if (item.isNew && !item.hadOriginalPrediction) return false;
          return true;
        })
        .map((item) => {
          if (item.originalIntent && predictionIntents.has(item.originalIntent)) {
            // Has original prediction → restore to it
            coveredPredictionLabels.add(item.originalIntent);
            return {
              ...item,
              intent: item.originalIntent,
              source: item.originalSource,
              isDeleted: false,
            };
          }
          // No original prediction (user-created, not new) → mark deleted
          return { ...item, isDeleted: true };
        });

      // Re-add original predictions not covered by any existing edit-state item
      for (const [predictionLabel, predictionInfo] of predictionIntents) {
        if (!coveredPredictionLabels.has(predictionLabel)) {
          newIntents.push({
            id: null,
            intent: predictionLabel,
            originalIntent: predictionLabel,
            source: predictionInfo.originalSource,
            originalSource: predictionInfo.originalSource,
            isDeleted: false,
            isNew: true,
            hadOriginalPrediction: true,
          });
        }
      }

      return { ...prev, intents: newIntents };
    });
  }, [originalPredictions]);

  // === Aspect Modifiers ===

  const updateAspect = useCallback((index: number, sentiment: SentimentLabel) => {
    setEditState((prev) => {
      if (!prev) return prev;
      const newAspects = [...prev.aspects];
      const item = newAspects[index];
      if (item) {
        // If sentiment matches original prediction, restore the true original source
        const matchesOriginal = item.originalSentiment && sentiment === item.originalSentiment;
        newAspects[index] = {
          ...item,
          sentiment,
          source: matchesOriginal ? item.originalSource : 'user',
        };
      }
      return { ...prev, aspects: newAspects };
    });
  }, []);

  const deleteAspect = useCallback((index: number) => {
    setEditState((prev) => {
      if (!prev) return prev;
      const newAspects = [...prev.aspects];
      if (newAspects[index]) {
        if (newAspects[index].isNew) {
          newAspects.splice(index, 1);
        } else {
          newAspects[index] = { ...newAspects[index], isDeleted: true };
        }
      }
      return { ...prev, aspects: newAspects };
    });
  }, []);

  const addAspect = useCallback((aspect: AspectLabel, sentiment: SentimentLabel) => {
    setEditState((prev) => {
      if (!prev || !originalPredictions) return prev;

      // Prevent duplicate: if this aspect is already active, do nothing
      if (prev.aspects.some((a) => !a.isDeleted && a.aspect === aspect)) {
        return prev;
      }

      // CHECK: Is this restoring a deleted predicted aspect?
      const deletedPredictionItem = prev.aspects.find(
        (a) => a.isDeleted && a.aspect === aspect
      );

      if (deletedPredictionItem) {
        // RESTORE the deleted item with the true original source
        const matchesOriginalSentiment = deletedPredictionItem.originalSentiment === sentiment;
        return {
          ...prev,
          aspects: prev.aspects.map((a) =>
            a === deletedPredictionItem
              ? {
                  ...a,
                  isDeleted: false,
                  sentiment,
                  source: matchesOriginalSentiment ? a.originalSource : ('user' as const),
                }
              : a
          ),
        };
      }

      // Check if this aspect+sentiment matches original prediction
      const originalAspectPrediction = originalPredictions.aspects.get(aspect);
      const matchesOriginal = originalAspectPrediction && originalAspectPrediction.sentiment === sentiment;

      // Use the tracked original source if this was a known prediction
      const resolvedOriginalSource = originalAspectPrediction?.originalSource || 'model';

      return {
        ...prev,
        aspects: [
          ...prev.aspects,
          {
            id: null,
            aspect,
            sentiment,
            originalSentiment: originalAspectPrediction?.sentiment || null,
            source: matchesOriginal ? resolvedOriginalSource : 'user',
            originalSource: resolvedOriginalSource,
            isDeleted: false,
            isNew: true,
            hadOriginalPrediction: !!originalAspectPrediction,
          },
        ],
      };
    });
  }, [originalPredictions]);

  const revertAspect = useCallback((index: number) => {
    setEditState((prev) => {
      if (!prev) return prev;
      const newAspects = [...prev.aspects];
      const item = newAspects[index];
      if (item && item.originalSentiment) {
        newAspects[index] = {
          ...item,
          sentiment: item.originalSentiment,
          // Restore the true original source (not hardcoded 'model')
          source: item.originalSource,
        };
      }
      return { ...prev, aspects: newAspects };
    });
  }, []);

  const revertAllAspects = useCallback(() => {
    setEditState((prev) => {
      if (!prev || !originalPredictions) return prev;

      const predictionAspects = originalPredictions.aspects;
      const coveredPredictionLabels = new Set<AspectLabel>();

      // Process existing edit-state items
      const newAspects = prev.aspects
        .filter((item) => {
          // User-created new items (no original prediction) → remove entirely
          if (item.isNew && !item.hadOriginalPrediction) return false;
          return true;
        })
        .map((item) => {
          const predictionInfo = predictionAspects.get(item.aspect);
          if (predictionInfo) {
            // Has original prediction → restore sentiment to it
            coveredPredictionLabels.add(item.aspect);
            return {
              ...item,
              sentiment: predictionInfo.sentiment,
              source: item.originalSource,
              isDeleted: false,
            };
          }
          // No original prediction (user-created, not new) → mark deleted
          return { ...item, isDeleted: true };
        });

      // Re-add original predictions not covered by any existing edit-state item
      for (const [predictionLabel, predictionInfo] of predictionAspects) {
        if (!coveredPredictionLabels.has(predictionLabel)) {
          newAspects.push({
            id: null,
            aspect: predictionLabel,
            sentiment: predictionInfo.sentiment,
            originalSentiment: predictionInfo.sentiment,
            source: predictionInfo.originalSource,
            originalSource: predictionInfo.originalSource,
            isDeleted: false,
            isNew: true,
            hadOriginalPrediction: true,
          });
        }
      }

      return { ...prev, aspects: newAspects };
    });
  }, [originalPredictions]);

  // === canRevert computed values ===

  const canRevertIntents = useMemo(() => {
    if (!editState || !originalPredictions) return false;

    const predictionIntents = originalPredictions.intents;
    const activeLabels = new Set(
      editState.intents.filter((i) => !i.isDeleted).map((i) => i.intent)
    );
    const predictionLabels = new Set(predictionIntents.keys());

    // Different set of labels → can revert
    if (activeLabels.size !== predictionLabels.size) return true;
    for (const label of activeLabels) {
      if (!predictionLabels.has(label)) return true;
    }
    for (const label of predictionLabels) {
      if (!activeLabels.has(label)) return true;
    }

    return false;
  }, [editState, originalPredictions]);

  const canRevertAspects = useMemo(() => {
    if (!editState || !originalPredictions) return false;

    const predictionAspects = originalPredictions.aspects;
    const activeAspects = editState.aspects.filter((a) => !a.isDeleted);

    // Check: user-added aspect exists (no original prediction)
    if (activeAspects.some((a) => !predictionAspects.has(a.aspect))) return true;

    // Check: original prediction deleted
    const activeAspectLabels = new Set(activeAspects.map((a) => a.aspect));
    for (const predictionLabel of predictionAspects.keys()) {
      if (!activeAspectLabels.has(predictionLabel)) return true;
    }

    // Check: any aspect's sentiment differs from original prediction
    for (const aspect of activeAspects) {
      const predictionInfo = predictionAspects.get(aspect.aspect);
      if (predictionInfo && aspect.sentiment !== predictionInfo.sentiment) return true;
    }

    return false;
  }, [editState, originalPredictions]);

  // === Validation ===

  const validation = useMemo(() => {
    if (!editState) return { canSave: false, error: null };

    const activeIntents = editState.intents.filter((i) => !i.isDeleted);
    if (activeIntents.length === 0) {
      return { canSave: false, error: 'ต้องมีอย่างน้อย 1 ประเภทข้อความ' };
    }

    const hasOffTopic = activeIntents.some((i) => i.intent === 'off_topic');
    if (hasOffTopic && activeIntents.length > 1) {
      return { canSave: false, error: '"นอกเรื่อง" ไม่สามารถใช้ร่วมกับประเภทอื่นได้' };
    }

    // Check for any actual changes from original state
    if (!originalFeedback) return { canSave: false, error: null };

    let hasChanges = false;

    // Check sentiment
    if (editState.sentiment && originalFeedback.sentiment_result) {
      if (editState.sentiment.sentiment !== originalFeedback.sentiment_result.sentiment) {
        hasChanges = true;
      }
    }

    // Check intents
    const originalIntents = originalFeedback.intent_results.filter((i) => !i.is_deleted);
    const activeEditIntents = editState.intents.filter((i) => !i.isDeleted);

    // Different count = change
    if (activeEditIntents.length !== originalIntents.length) {
      hasChanges = true;
    } else {
      // Check each intent
      for (const editIntent of activeEditIntents) {
        if (editIntent.isNew) {
          // New intent - check if it truly matches an original
          const matchesOriginal = originalIntents.some((o) => o.intent === editIntent.intent);
          if (!matchesOriginal) hasChanges = true;
        } else {
          const orig = originalIntents.find((o) => o.id === editIntent.id);
          if (!orig || orig.intent !== editIntent.intent) {
            hasChanges = true;
          }
        }
      }
      // Check if any original was deleted
      for (const orig of originalIntents) {
        const stillExists = activeEditIntents.some(
          (e) => e.id === orig.id || (e.isNew && e.intent === orig.intent)
        );
        if (!stillExists) hasChanges = true;
      }
    }

    // Check aspects
    const originalAspects = originalFeedback.aspect_results.filter((a) => !a.is_deleted);
    const activeEditAspects = editState.aspects.filter((a) => !a.isDeleted);

    if (activeEditAspects.length !== originalAspects.length) {
      hasChanges = true;
    } else {
      for (const editAspect of activeEditAspects) {
        if (editAspect.isNew) {
          const matchesOriginal = originalAspects.some(
            (o) => o.aspect === editAspect.aspect && o.sentiment === editAspect.sentiment
          );
          if (!matchesOriginal) hasChanges = true;
        } else {
          const orig = originalAspects.find((o) => o.id === editAspect.id);
          if (!orig || orig.sentiment !== editAspect.sentiment) {
            hasChanges = true;
          }
        }
      }
      for (const orig of originalAspects) {
        const stillExists = activeEditAspects.some(
          (e) => e.id === orig.id || (e.isNew && e.aspect === orig.aspect)
        );
        if (!stillExists) hasChanges = true;
      }
    }

    return { canSave: hasChanges, error: null };
  }, [editState, originalFeedback]);

  // === Derived Edit State (central source-of-truth for source badges) ===
  // Instead of relying on each mutation to compute the correct source,
  // we derive sources here from originalPredictions. This covers ALL user journeys:
  // delete+re-add, delete+change-dropdown, cross-record swaps, etc.
  const derivedEditState = useMemo((): AnalysisEditState | null => {
    if (!editState || !originalPredictions) return editState;

    return {
      ...editState,
      intents: editState.intents.map((intent) => {
        if (intent.isDeleted) return intent;

        // 1. Check if value matches this record's own original prediction
        if (intent.originalIntent && intent.intent === intent.originalIntent) {
          return { ...intent, source: intent.originalSource };
        }
        // 2. Check if value matches ANY original prediction (cross-record)
        const predictionInfo = originalPredictions.intents.get(intent.intent);
        if (predictionInfo) {
          return { ...intent, source: predictionInfo.originalSource };
        }
        // 3. No prediction match → user edit
        return { ...intent, source: 'user' as const };
      }),
      aspects: editState.aspects.map((aspect) => {
        if (aspect.isDeleted) return aspect;

        // 1. Check if sentiment matches this record's own original prediction
        if (aspect.originalSentiment && aspect.sentiment === aspect.originalSentiment) {
          return { ...aspect, source: aspect.originalSource };
        }
        // 2. Check if aspect+sentiment matches any original prediction
        const predictionInfo = originalPredictions.aspects.get(aspect.aspect);
        if (predictionInfo && predictionInfo.sentiment === aspect.sentiment) {
          return { ...aspect, source: predictionInfo.originalSource };
        }
        // 3. No prediction match → user edit
        return { ...aspect, source: 'user' as const };
      }),
    };
  }, [editState, originalPredictions]);

  // === Save Corrections ===

  const saveCorrections = useCallback(() => {
    if (!editState || !originalFeedback || !validation.canSave || !originalPredictions) return;

    const request: AnalysisCorrectionRequest = {};

    // === Sentiment ===
    if (editState.sentiment && originalFeedback.sentiment_result) {
      const currentVal = editState.sentiment.sentiment;
      const originalVal = originalFeedback.sentiment_result.sentiment;
      const predictionVal = editState.sentiment.originalSentiment;

      if (currentVal !== originalVal) {
        // Determine if this is a revert to original prediction
        const isRevertToPrediction = currentVal === predictionVal && originalVal !== predictionVal;
        request.sentiment = {
          sentiment: currentVal,
          revert: isRevertToPrediction,
        };
      }
    }

    // === Intents ===
    let intentCorrections: IntentCorrection[] = [];
    const originalIntents = originalFeedback.intent_results.filter((i) => !i.is_deleted);
    const activeEditIntents = editState.intents.filter((i) => !i.isDeleted);

    // Find deleted intents
    for (const intent of editState.intents) {
      if (intent.isDeleted && intent.id) {
        intentCorrections.push({ id: intent.id, intent: intent.intent, delete: true });
      }
    }

    // Find new or modified intents
    for (const intent of activeEditIntents) {
      if (intent.isNew) {
        // Check if this "new" intent is actually restoring an original prediction
        const matchesDeletedOriginal = originalIntents.some(
          (o) => !activeEditIntents.some((e) => e.id === o.id) && o.intent === intent.intent
        );

        if (!matchesDeletedOriginal) {
          // New intent — never send revert without id (schema rejects it).
          // Backend auto-detects original prediction match during resurrection.
          intentCorrections.push({
            intent: intent.intent,
          });
        }
        // If it matches a deleted original with same intent, it's a no-op (delete+add same)
      } else if (intent.id) {
        const orig = originalIntents.find((o) => o.id === intent.id);
        if (orig && orig.intent !== intent.intent) {
          const isRevertToPrediction = intent.originalIntent === intent.intent;
          intentCorrections.push({
            id: intent.id,
            intent: intent.intent,
            revert: isRevertToPrediction,
          });
        }
      }
    }

    // === Swap optimization for intents ===
    // When the user deletes a predicted record (e.g., "A") and changes
    // another record's dropdown to the same value (e.g., B→A), the naive
    // corrections [delete A-record, edit B-record→A] cause the backend to
    // set source='user' on the edited record. Instead, swap the operations:
    // keep the original prediction record (A) and delete the other (B).
    if (intentCorrections.length > 1) {
      const editCorrs = intentCorrections.filter((c) => !c.delete && c.id);
      const swappedEditIds = new Set<string>();
      const swappedDeleteIds = new Set<string>();
      const extraCorrections: IntentCorrection[] = [];

      for (const edit of editCorrs) {
        if (!edit.id) continue;
        // Find a deleted edit-state item whose original prediction matches this edit's new value
        const matchingDeleted = editState.intents.find(
          (d) =>
            d.isDeleted &&
            d.id &&
            d.originalIntent === edit.intent &&
            !swappedDeleteIds.has(d.id)
        );
        if (matchingDeleted?.id) {
          swappedEditIds.add(edit.id);
          swappedDeleteIds.add(matchingDeleted.id);
          // Delete the edited record instead of editing it
          extraCorrections.push({ id: edit.id, intent: edit.intent, delete: true });
          // If the prediction record was previously user-edited, revert it to original prediction
          if (matchingDeleted.intent !== matchingDeleted.originalIntent && matchingDeleted.originalIntent) {
            extraCorrections.push({
              id: matchingDeleted.id,
              intent: matchingDeleted.originalIntent,
              revert: true,
            });
          }
          // else: prediction record already has its original value, just don't delete it
        }
      }

      if (swappedEditIds.size > 0) {
        intentCorrections = [
          ...intentCorrections.filter((c) => {
            if (c.delete && c.id && swappedDeleteIds.has(c.id)) return false;
            if (!c.delete && c.id && swappedEditIds.has(c.id)) return false;
            return true;
          }),
          ...extraCorrections,
        ];
      }
    }

    if (intentCorrections.length > 0) {
      request.intents = intentCorrections;
    }

    // === Aspects ===
    const aspectCorrections: AspectCorrection[] = [];
    const originalAspects = originalFeedback.aspect_results.filter((a) => !a.is_deleted);
    const activeEditAspects = editState.aspects.filter((a) => !a.isDeleted);

    // Find deleted aspects
    for (const aspect of editState.aspects) {
      if (aspect.isDeleted && aspect.id) {
        aspectCorrections.push({
          id: aspect.id,
          aspect: aspect.aspect,
          sentiment: aspect.sentiment,
          delete: true,
        });
      }
    }

    // Find new or modified aspects
    for (const aspect of activeEditAspects) {
      if (aspect.isNew) {
        // Check if this matches a deleted original
        const matchesDeletedOriginal = originalAspects.some(
          (o) =>
            !activeEditAspects.some((e) => e.id === o.id) &&
            o.aspect === aspect.aspect &&
            o.sentiment === aspect.sentiment
        );

        if (!matchesDeletedOriginal) {
          // New aspect — never send revert without id (schema rejects it).
          // Backend auto-detects original prediction match during resurrection.
          aspectCorrections.push({
            aspect: aspect.aspect,
            sentiment: aspect.sentiment,
          });
        }
      } else if (aspect.id) {
        const orig = originalAspects.find((o) => o.id === aspect.id);
        if (orig && orig.sentiment !== aspect.sentiment) {
          const isRevertToPrediction = aspect.originalSentiment === aspect.sentiment;
          aspectCorrections.push({
            id: aspect.id,
            aspect: aspect.aspect,
            sentiment: aspect.sentiment,
            revert: isRevertToPrediction,
          });
        }
      }
    }

    if (aspectCorrections.length > 0) {
      request.aspects = aspectCorrections;
    }

    // Submit
    if (Object.keys(request).length > 0) {
      mutation.mutate(request);
    }
  }, [editState, originalFeedback, originalPredictions, validation.canSave, mutation]);

  return {
    isEditing,
    editState: derivedEditState,
    startEditing,
    cancelEditing,
    saveCorrections,
    updateSentiment,
    revertSentiment,
    updateIntent,
    deleteIntent,
    addIntent,
    revertIntent,
    updateAspect,
    deleteAspect,
    addAspect,
    revertAspect,
    revertAllIntents,
    revertAllAspects,
    canRevertIntents,
    canRevertAspects,
    canSave: validation.canSave,
    validationError: validation.error,
    isSaving: mutation.isPending,
    error: mutation.error as Error | null,
  };
}
