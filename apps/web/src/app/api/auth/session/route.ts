import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { token } = await request.json();
    
    // Set cookie that expires in 14 days
    const expiresIn = 60 * 60 * 24 * 14 * 1000;
    
    const response = NextResponse.json({ status: 'success' });
    response.cookies.set('auth_token', token, {
      maxAge: expiresIn / 1000,
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      path: '/',
      sameSite: 'lax',
    });

    return response;
  } catch (error) {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function DELETE() {
  const response = NextResponse.json({ status: 'success' });
  response.cookies.delete('auth_token');
  return response;
}
