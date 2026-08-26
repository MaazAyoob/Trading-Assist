import React, { useState, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { useMarketStore } from '../../stores/marketStore';
import { ChevronDown, Zap, BarChart2, Target, Waves, Mountain } from 'lucide-react';

interface ProfileItem {
  id: string;
  name: string;
  tf: string;
  context: string;
  desc: string;
  icon: React.ElementType;
}

const PROFILES: ProfileItem[] = [
  {
    id: 'SCALP_1M_V1',
    name: '⚡ SCALP',
    tf: '1m',
    context: '5m / 15m',
    desc: 'Short-duration momentum & micro pullback opportunity detection on 1m bars.',
    icon: Zap,
  },
  {
    id: 'INTRADAY_5M_V1',
    name: '📊 INTRADAY',
    tf: '5m',
    context: '15m / 1h',
    desc: 'Day-trading setups on 5m bars with 15m structure and 1h macro regime.',
    icon: BarChart2,
  },
  {
    id: 'TRADING_15M_V1',
    name: '🎯 TRADING',
    tf: '15m',
    context: '1h / 4h',
    desc: 'Medium-term intraday/same-day baseline trading analysis (Phase 5/8).',
    icon: Target,
  },
  {
    id: 'SWING_4H_V1',
    name: '🌊 SWING',
    tf: '4h',
    context: '1h / 1d',
    desc: 'Multi-day swing analysis emphasizing macro structure, S&R, and persistence.',
    icon: Waves,
  },
  {
    id: 'POSITION_1D_V1',
    name: '🏔️ POSITION',
    tf: '1d',
    context: '4h / 1w',
    desc: 'Longer-term analytical positioning on daily bars and macro cycles.',
    icon: Mountain,
  },
];

export const ProfileSelector: React.FC = () => {
  const { selectedProfileId, setProfile } = useMarketStore();
  const [isOpen, setIsOpen] = useState(false);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties>({});
  const buttonRef = useRef<HTMLButtonElement>(null);

  const currentProfile = PROFILES.find((p) => p.id === selectedProfileId) || PROFILES[0];
  const Icon = currentProfile.icon;

  // Compute fixed position from the button's bounding rect so the dropdown
  // escapes the header's backdrop-blur stacking context and stays within viewport on mobile.
  const openDropdown = () => {
    if (buttonRef.current) {
      const bRect = buttonRef.current.getBoundingClientRect();
      const dropdownWidth = Math.min(window.innerWidth - 24, 300);
      const left = Math.max(12, Math.min(bRect.left, window.innerWidth - dropdownWidth - 12));
      setRect(bRect);
      setDropdownStyle({
        position: 'fixed',
        top: bRect.bottom + 6,
        left,
        width: dropdownWidth,
        zIndex: 99999,
      });
    }
    setIsOpen(true);
  };

  // Keep dropdown anchored on scroll / resize
  useEffect(() => {
    if (!isOpen) return;
    const sync = () => {
      if (buttonRef.current) {
        const bRect = buttonRef.current.getBoundingClientRect();
        const dropdownWidth = Math.min(window.innerWidth - 24, 300);
        const left = Math.max(12, Math.min(bRect.left, window.innerWidth - dropdownWidth - 12));
        setRect(bRect);
        setDropdownStyle({
          position: 'fixed',
          top: bRect.bottom + 6,
          left,
          width: dropdownWidth,
          zIndex: 99999,
        });
      }
    };
    window.addEventListener('scroll', sync, true);
    window.addEventListener('resize', sync);
    return () => {
      window.removeEventListener('scroll', sync, true);
      window.removeEventListener('resize', sync);
    };
  }, [isOpen]);

  // ── Portal dropdown ──────────────────────────────────────────────────────────
  // Rendered straight into document.body so NO parent CSS (backdrop-filter,
  // overflow, transform, isolation) can affect it.
  const dropdownPortal =
    isOpen && rect
      ? ReactDOM.createPortal(
          <>
            {/* Transparent full-screen capture layer */}
            <div
              style={{ position: 'fixed', inset: 0, zIndex: 99998 }}
              onClick={() => setIsOpen(false)}
            />

            {/* The actual dropdown — sits at z-99999, always on top */}
            <div
              style={dropdownStyle}
              className="bg-slate-950 border border-slate-700 rounded-xl p-2 shadow-2xl space-y-1 max-h-[85vh] overflow-y-auto"
            >
              {/* Header row */}
              <div className="px-2 py-1 text-[10px] font-sans font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between border-b border-slate-800 pb-1 mb-1 select-none">
                <span>Trading Profile Horizon</span>
                <span className="text-indigo-400 font-mono">5 Horiz</span>
              </div>

              {PROFILES.map((p) => {
                const active = p.id === selectedProfileId;
                const PIcon = p.icon;
                return (
                  <button
                    key={p.id}
                    onClick={() => {
                      setProfile(p.id);
                      setIsOpen(false);
                    }}
                    className={`w-full text-left p-2 rounded-lg transition border flex flex-col gap-1 cursor-pointer ${
                      active
                        ? 'bg-indigo-950/60 border-indigo-500 text-white shadow-lg'
                        : 'bg-slate-900/40 border-transparent hover:bg-slate-900 hover:border-slate-800 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <PIcon
                          className={`w-3.5 h-3.5 ${active ? 'text-indigo-300' : 'text-slate-400'}`}
                        />
                        <span className="text-xs font-bold font-sans">{p.name}</span>
                      </div>
                      <div className="flex items-center gap-1 text-[10px] font-mono">
                        <span className="px-1.5 py-0.5 rounded bg-slate-950 text-indigo-300 font-bold">
                          {p.tf}
                        </span>
                        <span className="text-slate-500">ctx: {p.context}</span>
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-400 font-sans leading-tight line-clamp-2">
                      {p.desc}
                    </div>
                  </button>
                );
              })}
            </div>
          </>,
          document.body
        )
      : null;

  return (
    <div className="relative font-mono select-none">
      {/* Trigger button */}
      <button
        ref={buttonRef}
        onClick={() => (isOpen ? setIsOpen(false) : openDropdown())}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-indigo-500 text-slate-200 transition shadow-md"
        title="Select Analytical Trading Profile"
      >
        <div className="flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-xs font-bold font-sans">{currentProfile.name}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
            {currentProfile.tf}
          </span>
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-150 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Portal — mounted outside the React tree into document.body */}
      {dropdownPortal}
    </div>
  );
};
