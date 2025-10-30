'use client';

import React from 'react';
import { Box, Button, Container, Typography, Chip } from '@mui/material';
import { Build } from '@mui/icons-material';
import { getMerkleRoot, MerkleLevel } from '@/lib/utils/merkle';
import { getMerkleTree } from '@/lib/api/audit';
import MerkleTreeVisual, { transformLevelsToTreeData, TreeData } from '@/components/MerkleTreeVisual';

// removed HashBox (replaced by react-d3-tree based visualizer)

export default function MerkleVisualizerPage() {
  const [levels, setLevels] = React.useState<MerkleLevel[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [loadingFromBackend, setLoadingFromBackend] = React.useState(false);

  // Single action: fetch the current tree from backend (all entries)
  const handleFetch = async () => {
    setError(null);
    setLoadingFromBackend(true);
    try {
      const data = await getMerkleTree('all');
      setLevels(data.levels.map((lvl: string[]) => lvl.map((h: string) => (h.startsWith('0x') ? h.slice(2) : h))));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load Merkle tree from backend';
      setError(msg);
    } finally {
      setLoadingFromBackend(false);
    }
  };

  const merkleRoot = getMerkleRoot(levels);
  const treeData: TreeData | null = React.useMemo(() => transformLevelsToTreeData(levels), [levels]);

  

  return (
    <Container maxWidth="xl" sx={{ py: 0, height: 'calc(100vh - 64px)' }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <Box sx={{ p: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button variant="contained" startIcon={<Build />} onClick={handleFetch} disabled={loadingFromBackend}>
            {loadingFromBackend ? 'Fetching...' : 'Fetch Tree'}
          </Button>
          {merkleRoot && (
            <Chip size="small" color="primary" label={`Root: ${merkleRoot}`} sx={{ fontFamily: 'monospace' }} />
          )}
          {error && (
            <Typography variant="body2" color="error">
              {error}
            </Typography>
          )}
        </Box>
        <Box sx={{ flexGrow: 1, width: '100%', height: '100%' }}>
          {levels.length === 0 || !treeData ? (
            <Box sx={{ color: 'text.secondary', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              Click &quot;Fetch Tree&quot; to load and visualize the current Merkle tree
            </Box>
          ) : (
            <MerkleTreeVisual data={treeData} />
          )}
        </Box>
      </Box>
    </Container>
  );
}


