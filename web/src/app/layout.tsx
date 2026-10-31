import React from 'react';

export const metadata = {
  title: 'DISHA — Student Early-Warning & Intervention Platform',
  description: 'Enterprise Early-Warning and Accountable Intervention Platform for Student Success',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}
