import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'PADI.AI - Adaptive Math Learning',
  description: 'Personalized AI-powered math learning for Oregon elementary students',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`font-sans antialiased bg-gray-50`}>
        {children}
      </body>
    </html>
  );
}
