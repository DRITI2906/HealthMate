import { Activity, Moon, Droplets, TrendingUp, TrendingDown, Minus, MinusCircle, Edit2, Plus, PlusCircle, Check, Target } from 'lucide-react';

import { useState, useEffect } from 'react';
import { Button } from '../ui/Button';
import { useHealth } from '../../contexts/HealthContext';
import confetti from 'canvas-confetti';

const getIcon = (name: string) => {
  switch (name) {
    case 'Sleep Quality': return <Moon className="w-5 h-5" />;
    case 'Hydration': return <Droplets className="w-5 h-5" />;
    default: return <Activity className="w-5 h-5" />;
  }
};

const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'up': return <TrendingUp className="w-4 h-4 text-green-500" />;
    case 'down': return <TrendingDown className="w-4 h-4 text-red-500" />;
    default: return <Minus className="w-4 h-4 text-gray-400 dark:text-gray-500" />;
  }
};

export function HealthMetrics() {
  console.log('HealthMetrics component rendering');
  
  try {
    const { metrics, updateMetric, updateTarget, incrementHydration, decrementHydration } = useHealth();
    
    const [editingMetric, setEditingMetric] = useState<string | null>(null);
    const [editingTarget, setEditingTarget] = useState<string | null>(null);
    const [tempValue, setTempValue] = useState<number>(0);
    const [tempTarget, setTempTarget] = useState<number>(0);
    const [showingCelebration, setShowingCelebration] = useState<string[]>([]);
    const [achievedTargets, setAchievedTargets] = useState<Record<string, boolean>>({});
    const [isInitialized, setIsInitialized] = useState(false);

    // Initialize achievement status on mount
    useEffect(() => {
      if (!metrics || metrics.length === 0) return;
      
      const initialAchievements = metrics.reduce((acc, metric) => {
        acc[metric.id] = metric.target != null && metric.value >= metric.target;
        return acc;
      }, {} as Record<string, boolean>);
      
      setAchievedTargets(initialAchievements);
      setIsInitialized(true);
    }, [metrics]);

    // Track previous values to detect when targets are newly reached
    useEffect(() => {
      if (!isInitialized || !metrics || metrics.length === 0) return;

      metrics.forEach(metric => {
        const wasAchieved = achievedTargets[metric.id];
        const isAchieved = metric.target != null && metric.value >= metric.target;

        if (isAchieved && !wasAchieved && !showingCelebration.includes(metric.id)) {
          setShowingCelebration(prev => [...prev, metric.id]);
          
          if (metric.name === 'Hydration') {
            confetti({
              particleCount: 150,
              spread: 70,
              origin: { x: 0.5, y: 0.5 },
              startVelocity: 45,
              gravity: 0.8,
              ticks: 120,
              colors: ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#ff8800', '#8800ff'],
              shapes: ['circle', 'square'],
              scalar: 2.5
            });
          }
          
          setTimeout(() => {
            setShowingCelebration(prev => prev.filter(id => id !== metric.id));
          }, 2000);
        }

        setAchievedTargets(prev => ({
          ...prev,
          [metric.id]: isAchieved
        }));
      });
    }, [metrics, isInitialized, achievedTargets]);

    const handleEdit = (metricId: string, value: number, isTarget: boolean = false) => {
      if (isTarget) {
        setEditingTarget(metricId);
        setTempTarget(value);
      } else {
        setEditingMetric(metricId);
        setTempValue(value);
      }
    };

    const handleSave = (metricId: string, isTarget: boolean = false) => {
      if (isTarget) {
        updateTarget(metricId, tempTarget);
        setEditingTarget(null);
      } else {
        updateMetric(metricId, tempValue);
        setEditingMetric(null);
      }
    };

    // Filter out Wellness Score & Symptom Checks before rendering
    const filteredMetrics = metrics?.filter(
      (metric) => metric.name !== 'Wellness Score' && metric.name !== 'Symptom Checks'
    );

    if (!filteredMetrics || filteredMetrics.length === 0) {
      return (
        <div className="h-full bg-white dark:bg-gray-800 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <div>No health metrics available</div>
            <div className="text-sm mt-1">Please check the HealthContext</div>
          </div>
        </div>
      );
    }

    return (
      <div className="h-full bg-white dark:bg-gray-800">
        <div className="border-b border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Health Metrics</h2>
          <p className="text-gray-600 dark:text-gray-300 mt-1">Real-time health data overview</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {filteredMetrics.map((metric) => (
              <div key={metric.id} data-metric-id={metric.id} className="relative bg-gradient-to-br from-gray-50 to-green-50 dark:from-gray-800 dark:to-gray-700 p-4 rounded-lg border border-gray-100 dark:border-gray-700 transition-colors duration-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-gray-600 dark:text-gray-400">{getIcon(metric.name)}</div>
                  {getTrendIcon(metric.trend)}
                </div>
                
                {metric.name === 'Hydration' && showingCelebration.includes(metric.id) && (
                  <div className="absolute -top-2 -right-2 z-10">
                    <div className="animate-bounce text-2xl">🎉</div>
                  </div>
                )}
                <div className="space-y-1">
                  {editingMetric === metric.id ? (
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        value={tempValue}
                        onChange={(e) => setTempValue(Number(e.target.value))}
                        className="w-20 px-2 py-1 text-lg border rounded dark:bg-gray-700 dark:border-gray-600"
                      />
                      <Button
                        onClick={() => handleSave(metric.id)}
                        size="sm"
                        variant="ghost"
                        className="p-1"
                      >
                        <Check className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between">
                      <p className="text-2xl font-bold text-gray-800 dark:text-gray-100">
                        {metric.value}
                        <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-1">{metric.unit}</span>
                      </p>
                      {(metric.name === 'Sleep Quality' || metric.name === 'Hydration') && (
                        <div className="flex gap-1">
                          {metric.name === 'Hydration' ? (
                            <>
                              <Button
                                onClick={decrementHydration}
                                size="sm"
                                variant="ghost"
                                className="p-1"
                              >
                                <MinusCircle className="w-4 h-4" />
                              </Button>
                              <Button
                                onClick={incrementHydration}
                                size="sm"
                                variant="ghost"
                                className="p-1"
                              >
                                <PlusCircle className="w-4 h-4" />
                              </Button>
                            </>
                          ) : (
                            <Button
                              onClick={() => handleEdit(metric.id, metric.value)}
                              size="sm"
                              variant="ghost"
                              className="p-1"
                            >
                              <Edit2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  <p className="text-sm text-gray-600 dark:text-gray-300">{metric.name}</p>
                  {metric.target !== null && (
                    <div className="flex items-center justify-between">
                      {editingTarget === metric.id ? (
                        <div className="flex items-center space-x-2">
                          <input
                            type="number"
                            value={tempTarget}
                            onChange={(e) => setTempTarget(Number(e.target.value))}
                            className="w-16 px-2 py-1 text-xs border rounded dark:bg-gray-700 dark:border-gray-600"
                          />
                          <Button
                            onClick={() => handleSave(metric.id, true)}
                            size="sm"
                            variant="ghost"
                            className="p-1"
                          >
                            <Check className="w-3 h-3" />
                          </Button>
                        </div>
                      ) : (
                        <>
                          <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                            Target: {metric.target} {metric.unit}
                          </p>
                          <Button
                            onClick={() => handleEdit(metric.id, metric.target || 0, true)}
                            size="sm"
                            variant="ghost"
                            className="p-1"
                          >
                            <Target className="w-3 h-3" />
                          </Button>
                        </>
                      )}
                    </div>
                  )}
                  <p className="text-xs text-gray-400 dark:text-gray-500">
                    Last updated: {new Date(metric.lastUpdated).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  } catch (error) {
    console.error('HealthMetrics component error:', error);
    return (
      <div className="h-full bg-white dark:bg-gray-800 flex items-center justify-center">
        <div className="text-center text-red-500">
          <div>Error rendering HealthMetrics</div>
          <div className="text-sm mt-1">{error instanceof Error ? error.message : 'Unknown error'}</div>
        </div>
      </div>
    );
  }
}
