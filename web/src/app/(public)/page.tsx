import React from 'react';

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 text-center">
      <h1 className="text-4xl font-extrabold tracking-tight text-blue-600 sm:text-5xl">
        DISHA Platform
      </h1>
      <p className="mt-4 max-w-xl text-lg text-slate-600">
        No Alert Without Action — Converting student observations into accountable interventions.
      </p>
      <div className="mt-8 flex gap-4">
        <a href="/auth/login" className="rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white shadow hover:bg-blue-700">
          Sign In
        </a>
      </div>
    </main>
  );
}
