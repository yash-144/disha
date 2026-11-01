import React from 'react';
import Link from 'next/link';

export function AdminNav() {
  const links = [
    { label: 'Overview', href: '/admin-dashboard' },
    { label: 'User Directory', href: '/users' },
    { label: 'Case Supervision', href: '/cases' },
    { label: 'Data Imports', href: '/imports' },
    { label: 'Audit Trail', href: '/audit' },
    { label: 'Settings', href: '/settings' },
  ];

  return (
    <nav className="flex space-x-4 border-b border-gray-200 pb-3 mb-6">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className="text-sm font-medium text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md hover:bg-gray-100 transition"
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
