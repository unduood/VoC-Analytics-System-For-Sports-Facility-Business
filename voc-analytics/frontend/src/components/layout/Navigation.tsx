'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BarChart3, FileText, PlusCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  {
    name: 'Overall Dashboard',
    nameTh: 'ภาพรวม',
    href: '/dashboard',
    icon: BarChart3,
  },
  {
    name: 'View Records',
    nameTh: 'ดูข้อมูล',
    href: '/records',
    icon: FileText,
  },
  {
    name: 'Manual Input',
    nameTh: 'บันทึกเอง',
    href: '/manual',
    icon: PlusCircle,
  },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center space-x-2 px-1 py-4 border-b-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <Icon className="w-4 h-4" />
                <span>{item.nameTh}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
