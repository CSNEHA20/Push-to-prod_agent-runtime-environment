import React from 'react';
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  RotateCcw,
  Gauge
} from 'lucide-react';

export default function ReplayControls({
  isPlaying = false,
  onPlayToggle,
  currentStepIndex = 0,
  totalSteps = 1,
  onStepChange,
  playbackSpeed = 1,
  onSpeedChange
}) {
  const currentStepNumber = Math.min(totalSteps, currentStepIndex + 1);

  const handleStepBack = () => {
    if (currentStepIndex > 0 && onStepChange) {
      onStepChange(currentStepIndex - 1);
    }
  };

  const handleStepForward = () => {
    if (currentStepIndex < totalSteps - 1 && onStepChange) {
      onStepChange(currentStepIndex + 1);
    }
  };

  const handleReset = () => {
    if (onStepChange) {
      onStepChange(0);
    }
  };

  const handleSliderChange = (e) => {
    const val = parseInt(e.target.value, 10);
    if (!isNaN(val) && onStepChange) {
      onStepChange(val - 1);
    }
  };

  const speeds = [0.5, 1, 2];

  return (
    <div className="bg-arc-surface border border-arc-outline rounded-xl p-4 shadow-xl font-mono text-xs text-arc-textPrimary flex flex-col md:flex-row items-center justify-between gap-4">
      {/* Playback Action Buttons */}
      <div className="flex items-center space-x-2 shrink-0">
        {/* Reset / Restart */}
        <button
          onClick={handleReset}
          title="Reset to Step 1"
          className="p-2 rounded-lg bg-arc-bg border border-arc-outline hover:border-arc-primary/50 text-arc-textSecondary hover:text-arc-textPrimary transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Step Back */}
        <button
          onClick={handleStepBack}
          disabled={currentStepIndex <= 0}
          title="Step Back"
          className="p-2 rounded-lg bg-arc-bg border border-arc-outline hover:border-arc-primary/50 disabled:opacity-40 disabled:hover:border-arc-outline text-arc-textSecondary hover:text-arc-textPrimary transition-colors"
        >
          <SkipBack className="w-4 h-4" />
        </button>

        {/* Play/Pause */}
        <button
          onClick={onPlayToggle}
          title={isPlaying ? 'Pause Replay' : 'Play Replay'}
          className={`p-2.5 rounded-xl font-bold flex items-center justify-center transition-all ${
            isPlaying
              ? 'bg-amber-500 text-slate-950 shadow-lg shadow-amber-500/20 animate-pulse'
              : 'bg-arc-primary text-slate-950 shadow-lg shadow-arc-primary/20 hover:bg-arc-primary/90'
          }`}
        >
          {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
        </button>

        {/* Step Forward */}
        <button
          onClick={handleStepForward}
          disabled={currentStepIndex >= totalSteps - 1}
          title="Step Forward"
          className="p-2 rounded-lg bg-arc-bg border border-arc-outline hover:border-arc-primary/50 disabled:opacity-40 disabled:hover:border-arc-outline text-arc-textSecondary hover:text-arc-textPrimary transition-colors"
        >
          <SkipForward className="w-4 h-4" />
        </button>
      </div>

      {/* Progress Bar Slider & Counter */}
      <div className="flex-1 w-full max-w-xl flex items-center gap-3">
        <span className="text-[11px] font-bold text-arc-primary shrink-0 min-w-[75px] text-right">
          Step {totalSteps > 0 ? currentStepNumber : 0} / {totalSteps}
        </span>

        <div className="relative flex-1 flex items-center">
          <input
            type="range"
            min="1"
            max={Math.max(1, totalSteps)}
            value={totalSteps > 0 ? currentStepNumber : 1}
            onChange={handleSliderChange}
            disabled={totalSteps <= 1}
            className="w-full h-2 bg-arc-bg rounded-lg appearance-none cursor-pointer border border-arc-outline accent-arc-primary disabled:opacity-50"
          />
        </div>
      </div>

      {/* Speed Controls */}
      <div className="flex items-center space-x-1.5 shrink-0 bg-arc-bg border border-arc-outline p-1 rounded-lg">
        <Gauge className="w-3.5 h-3.5 text-arc-textSecondary ml-1 mr-0.5" />
        {speeds.map((spd) => (
          <button
            key={spd}
            onClick={() => onSpeedChange && onSpeedChange(spd)}
            className={`px-2 py-1 rounded text-[10px] font-bold transition-colors ${
              playbackSpeed === spd
                ? 'bg-arc-primary text-slate-950 shadow-sm'
                : 'text-arc-textSecondary hover:text-arc-textPrimary hover:bg-arc-outline/50'
            }`}
          >
            {spd}x
          </button>
        ))}
      </div>
    </div>
  );
}
