import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('disha_session')?.value;
  const { pathname } = request.nextUrl;

  // Protect internal routes
  if ((pathname.startsWith('/dashboard') || pathname.startsWith('/admin')) && !token) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
