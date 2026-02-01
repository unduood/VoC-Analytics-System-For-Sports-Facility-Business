'use client';

import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import Image from 'next/image';
import { formatRelativeTime } from '@/lib/utils';
import { useRealtime } from '@/hooks/useRealtime';
import { useApiHealth } from '@/hooks/useApiHealth';

export function Header() {
  const { isConnected, connectionStatus, lastUpdate, reconnect } = useRealtime();
  const { status: apiStatus, isHealthy: isApiHealthy, refetch: refetchHealth } = useApiHealth();
  const [displayTime, setDisplayTime] = useState<string>('');

  useEffect(() => {
    // Update display time every 10 seconds
    const updateTime = () => {
      if (lastUpdate) {
        setDisplayTime(formatRelativeTime(lastUpdate));
      } else {
        setDisplayTime('');
      }
    };
    updateTime();
    const interval = setInterval(updateTime, 10000);
    return () => clearInterval(interval);
  }, [lastUpdate]);

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-4">
          <div className="flex items-center space-x-4">
            <Image
              src="/logo.svg"
              alt="Logo"
              width={72}
              height={72}
              className="rounded-xl"
            />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Gymini Fitness Club
              </h1>
              <p className="text-sm text-gray-500">
                Voice of Customer Analytics System
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-sm">
            {/* System Status - Simple display */}
            {isApiHealthy && isConnected ? (
              <div className="flex items-center space-x-1.5 text-green-600">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span>ออนไลน์</span>
              </div>
            ) : connectionStatus === "connecting" ||
              apiStatus === "checking" ? (
              <div className="flex items-center space-x-1.5 text-yellow-600">
                <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
                <span>กำลังเชื่อมต่อ</span>
              </div>
            ) : (
              <button
                onClick={() => {
                  if (!isApiHealthy) refetchHealth();
                  if (!isConnected) reconnect();
                }}
                className="flex items-center space-x-1.5 text-red-600 hover:text-red-700"
              >
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span>ออฟไลน์</span>
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            )}

            {lastUpdate && (
              <>
                <span className="text-gray-300 hidden sm:inline">|</span>
                <span className="text-gray-500 hidden sm:inline">
                  อัปเดต{displayTime}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
