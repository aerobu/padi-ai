import type { Metadata } from 'next';
import { Playfair_Display, Inter } from 'next/font/google';
import './globals.css';

const playfair = Playfair_Display({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-display',
  weight: ['700', '800'],
});

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
  weight: ['400', '500', '600', '700'],
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
    <html lang="en" className={`${playfair.variable} ${inter.variable} no-js`}>
      <body className={`font-sans antialiased bg-page text-neutral-900 ${playfair.variable} ${inter.variable}`}>
        {children}
      </body>
    </html>
  );
}
