/**
 * Root Layout - Wraps entire application with providers and theme
 */

import React from 'react';
import { Providers } from '@/components/common/Providers';
import { NavBar } from '@/components/common/NavBar';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <NavBar />
          {children}
        </Providers>
      </body>
    </html>
  );
}
