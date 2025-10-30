'use client';

/**
 * Activity Panel - Collapsible right panel showing system operations
 * Displays real-time steps for handshake, claim submission, fraud detection, etc.
 */

import React, { useState } from 'react';
import {
  Drawer,
  Box,
  IconButton,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
  Paper,
  Collapse,
  Tooltip,
} from '@mui/material';
import {
  ChevronLeft,
  ChevronRight,
  Security,
  Send,
  Psychology,
  Link as LinkIcon,
  CheckCircle,
  Error as ErrorIcon,
  Sync,
  Timer,
} from '@mui/icons-material';
import { useActivityLog } from '@/contexts/ActivityContext';

const DRAWER_WIDTH = 400;

export function ActivityPanel() {
  const [open, setOpen] = useState(true);
  const { activities, clearActivities } = useActivityLog();

  const getStepIcon = (stepType: string) => {
    switch (stepType) {
      case 'handshake':
        return <Security color="primary" />;
      case 'claim_submit':
        return <Send color="primary" />;
      case 'fraud_detection':
        return <Psychology color="warning" />;
      case 'log_entry':
        return <LinkIcon color="success" />;
      case 'checkpoint':
        return <Security color="success" />;
      case 'verification':
        return <CheckCircle color="success" />;
      default:
        return <Sync color="action" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle fontSize="small" color="success" />;
      case 'error':
        return <ErrorIcon fontSize="small" color="error" />;
      case 'pending':
        return <Sync fontSize="small" color="warning" sx={{ animation: 'spin 2s linear infinite', '@keyframes spin': { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } } }} />;
      default:
        return <Timer fontSize="small" color="action" />;
    }
  };

  const getStatusColor = (status: string): "success" | "error" | "warning" | "default" => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <>
      <Drawer
        anchor="right"
        open={open}
        variant="persistent"
        sx={{
          width: open ? DRAWER_WIDTH : 0,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            mt: 8, // Account for navbar
            height: 'calc(100vh - 64px)',
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', p: 2, justifyContent: 'space-between' }}>
          <Typography variant="h6" component="div">
            System Activity
          </Typography>
          <Box>
            <Tooltip title="Clear logs">
            <IconButton size="small" onClick={clearActivities} sx={{ mr: 1 }} title="Clear activity log">
              <ErrorIcon fontSize="small" />
            </IconButton>
            </Tooltip>
            <IconButton onClick={() => setOpen(false)}>
              <ChevronRight />
            </IconButton>
          </Box>
        </Box>
        <Divider />

        <Box sx={{ overflow: 'auto', flex: 1, p: 2 }}>
          {activities.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'background.default' }}>
              <Typography variant="body2" color="text.secondary">
                No activity yet. Perform actions to see the system flow.
              </Typography>
            </Paper>
          ) : (
            <List>
              {activities.map((activity, index) => (
                <React.Fragment key={activity.id}>
                  <ListItem
                    sx={{
                      mb: 1,
                      bgcolor: activity.status === 'error' ? 'error.light' : 
                               activity.status === 'completed' ? 'success.light' :
                               activity.status === 'pending' ? 'warning.light' : 'background.paper',
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                    }}
                  >
                    <ListItemIcon>{getStepIcon(activity.type)}</ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography variant="subtitle2">{activity.title}</Typography>
                          {getStatusIcon(activity.status)}
                          <Chip
                            label={activity.status}
                            size="small"
                            color={getStatusColor(activity.status)}
                            sx={{ ml: 'auto' }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {activity.description}
                          </Typography>
                          {activity.details && (
                            <Collapse in={true}>
                              <Paper
                                sx={{
                                  mt: 1,
                                  p: 1.5,
                                  bgcolor: 'background.default',
                                  fontSize: '0.75rem',
                                  fontFamily: 'monospace',
                                  maxHeight: 200,
                                  overflow: 'auto',
                                }}
                              >
                                {typeof activity.details === 'string' ? (
                                  <Typography variant="caption" component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap' }}>
                                    {activity.details}
                                  </Typography>
                                ) : (
                                  <Typography variant="caption" component="pre" sx={{ m: 0 }}>
                                    {JSON.stringify(activity.details, null, 2)}
                                  </Typography>
                                )}
                              </Paper>
                            </Collapse>
                          )}
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                            {activity.timestamp 
                              ? (() => {
                                  const timeDiff = Date.now() - new Date(activity.timestamp).getTime();
                                  const seconds = Math.floor(timeDiff / 1000);
                                  const minutes = Math.floor(seconds / 60);
                                  const hours = Math.floor(minutes / 60);
                                  if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
                                  if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
                                  return `${seconds} second${seconds !== 1 ? 's' : ''} ago`;
                                })()
                              : 'Just now'}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < activities.length - 1 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
            </List>
          )}
        </Box>
      </Drawer>

      {!open && (
        <IconButton
          onClick={() => setOpen(true)}
          sx={{
            position: 'fixed',
            right: 0,
            top: '50%',
            transform: 'translateY(-50%)',
            zIndex: 1200,
            bgcolor: 'primary.main',
            color: 'primary.contrastText',
            '&:hover': {
              bgcolor: 'primary.dark',
            },
            borderRadius: '4px 0 0 4px',
          }}
        >
          <ChevronLeft />
        </IconButton>
      )}
    </>
  );
}

