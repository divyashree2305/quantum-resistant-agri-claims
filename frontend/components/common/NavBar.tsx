'use client';

/**
 * Navigation Bar Component
 */

import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Brightness4,
  Brightness7,
  Language,
  Logout,
} from '@mui/icons-material';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useSession } from '@/contexts/SessionContext';
import { SecurityBadge } from './SecurityBadge';

export function NavBar() {
  const { mode, toggleTheme } = useTheme();
  const { locale, setLocale } = useLanguage();
  const { clearSession } = useSession();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleLanguageMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleLanguageMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLanguageChange = (newLocale: 'en' | 'es') => {
    setLocale(newLocale);
    handleLanguageMenuClose();
  };

  return (
    <AppBar position="static" elevation={0}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Insurance Claim System
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SecurityBadge />

          <IconButton onClick={handleLanguageMenuOpen} color="inherit">
            <Language />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleLanguageMenuClose}
          >
            <MenuItem
              onClick={() => handleLanguageChange('en')}
              selected={locale === 'en'}
            >
              English
            </MenuItem>
            <MenuItem
              onClick={() => handleLanguageChange('es')}
              selected={locale === 'es'}
            >
              Español
            </MenuItem>
          </Menu>

          <IconButton onClick={toggleTheme} color="inherit">
            {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
          </IconButton>

          <IconButton onClick={clearSession} color="inherit">
            <Logout />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

