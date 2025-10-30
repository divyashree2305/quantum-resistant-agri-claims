'use client';

import React from 'react';
import Tree from 'react-d3-tree';
import type { RawNodeDatum, CustomNodeElementProps } from 'react-d3-tree';
import { useTheme, type Theme } from '@mui/material/styles';
import { Box, Paper, Typography, Divider } from '@mui/material';

export interface TreeData {
  name: string;
  attributes?: { [key: string]: string | boolean | number };
  children?: TreeData[];
}

/**
 * Transform bottom-up levels (level[0]=leaves) to top-down hierarchical data for react-d3-tree.
 */
export function transformLevelsToTreeData(levels: string[][]): TreeData | null {
  if (!levels || levels.length === 0) return null;

  const buildNode = (levelIdx: number, nodeIdx: number): TreeData => {
    const hash = levels[levelIdx][nodeIdx];
    const isRoot = levelIdx === levels.length - 1 && nodeIdx === 0;
    const isLeaf = levelIdx === 0;
    const totalLevels = levels.length;
    const nodeType = isRoot ? 'root' : isLeaf ? 'leaf' : 'internal';

    const node: TreeData = {
      name: `0x${hash.substring(0, 10)}...`,
      attributes: { 
        hash: `0x${hash}`, 
        isRoot,
        isLeaf,
        nodeType,
        level: levelIdx,
        levelFromRoot: totalLevels - 1 - levelIdx,
        nodeIndex: nodeIdx,
        hashLength: hash.length,
        hashAlgorithm: 'SHA3-256'
      },
      children: [],
    };

    if (levelIdx === 0) return node; // leaf

    const leftChildIdx = nodeIdx * 2;
    const rightChildIdx = nodeIdx * 2 + 1;
    const prevLevel = levels[levelIdx - 1];

    if (leftChildIdx < prevLevel.length) {
      node.children!.push(buildNode(levelIdx - 1, leftChildIdx));
    }
    if (rightChildIdx < prevLevel.length) {
      node.children!.push(buildNode(levelIdx - 1, rightChildIdx));
    } else if (leftChildIdx < prevLevel.length) {
      // odd duplication case
      node.children!.push(buildNode(levelIdx - 1, leftChildIdx));
    }

    return node;
  };

  return buildNode(levels.length - 1, 0);
}

type MinimalNodeDatum = { name?: string; attributes?: Record<string, unknown> };

interface TooltipInfo {
  hash: string;
  nodeType: string;
  level: number;
  levelFromRoot: number;
  nodeIndex: number;
  hashLength: number;
  hashAlgorithm: string;
  x: number;
  y: number;
}

function RenderCustomNode({ 
  nodeDatum, 
  theme,
  onMouseEnter,
  onMouseLeave
}: { 
  nodeDatum: MinimalNodeDatum; 
  theme: Theme;
  onMouseEnter: (info: TooltipInfo) => void;
  onMouseLeave: () => void;
}) {
  const handleMouseEnter = (e: React.MouseEvent<SVGGElement>) => {
    const info: TooltipInfo = {
      hash: String(nodeDatum.attributes?.hash ?? ''),
      nodeType: String(nodeDatum.attributes?.nodeType ?? 'unknown'),
      level: Number(nodeDatum.attributes?.level ?? 0),
      levelFromRoot: Number(nodeDatum.attributes?.levelFromRoot ?? 0),
      nodeIndex: Number(nodeDatum.attributes?.nodeIndex ?? 0),
      hashLength: Number(nodeDatum.attributes?.hashLength ?? 0),
      hashAlgorithm: String(nodeDatum.attributes?.hashAlgorithm ?? 'SHA3-256'),
      x: e.clientX,
      y: e.clientY
    };
    
    onMouseEnter(info);
  };

  const handleMouseLeave = () => {
    onMouseLeave();
  };

  const isRoot = nodeDatum.attributes?.isRoot as boolean;
  const isLeaf = nodeDatum.attributes?.isLeaf as boolean;

  return (
    <g
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{ cursor: 'pointer' }}
    >
      <rect
        width="150"
        height="30"
        x={-75}
        y={-15}
        rx={4}
        fill={isRoot ? theme.palette.primary.main : isLeaf ? theme.palette.secondary.light : theme.palette.background.paper}
        stroke={theme.palette.divider}
        strokeWidth={isRoot ? 2 : 1}
        opacity={0.9}
      />
      <text
        x={0}
        y={0}
        dy={'.35em'}
        textAnchor={'middle'}
        fill={isRoot ? theme.palette.primary.contrastText : theme.palette.text.primary}
        style={{ fontFamily: 'monospace', fontSize: '12px', pointerEvents: 'none' }}
      >
        {nodeDatum.name}
      </text>
      <title>{String(nodeDatum.attributes?.hash ?? '')}</title>
    </g>
  );
}

export default function MerkleTreeVisual({ data }: { data: TreeData }) {
  const theme = useTheme();
  const [translate, setTranslate] = React.useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [tooltipInfo, setTooltipInfo] = React.useState<TooltipInfo | null>(null);
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (containerRef.current) {
      const { width } = containerRef.current.getBoundingClientRect();
      setTranslate({ x: width / 2, y: 60 });
    }
  }, []);

  const handleMouseEnter = (info: TooltipInfo) => {
    setTooltipInfo(info);
  };

  const handleMouseLeave = () => {
    setTooltipInfo(null);
  };

  const formatHash = (hash: string) => {
    if (!hash) return '';
    // Remove 0x prefix if present for display
    const cleanHash = hash.startsWith('0x') ? hash.slice(2) : hash;
    // Format as blocks of 8 characters
    return cleanHash.match(/.{1,8}/g)?.join(' ') || cleanHash;
  };

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Tree
        data={data as unknown as RawNodeDatum}
        orientation="vertical"
        pathFunc="step"
        translate={translate}
        collapsible={false}
        separation={{ siblings: 1.2, nonSiblings: 1.5 }}
        renderCustomNodeElement={(rd3tProps: CustomNodeElementProps) => (
          <RenderCustomNode 
            nodeDatum={rd3tProps.nodeDatum as unknown as MinimalNodeDatum} 
            theme={theme}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          />
        )}
      />
      
      {tooltipInfo && (
        <Box
          component={Paper}
          elevation={8}
          sx={{
            position: 'fixed',
            left: tooltipInfo.x + 15,
            top: tooltipInfo.y - 10,
            zIndex: 10000,
            p: 2,
            minWidth: 320,
            maxWidth: 400,
            pointerEvents: 'none',
            backgroundColor: theme.palette.mode === 'dark' ? 'rgba(30, 30, 30, 0.95)' : 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(8px)',
          }}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, textTransform: 'capitalize' }}>
            {tooltipInfo.nodeType} Node
          </Typography>
          <Divider sx={{ mb: 1.5 }} />
          
          <Box sx={{ mb: 1.5 }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>
              Full Hash
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', wordBreak: 'break-all' }}>
              {formatHash(tooltipInfo.hash)}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Level (from bottom):
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                {tooltipInfo.level}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Level (from root):
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                {tooltipInfo.levelFromRoot}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Node Index:
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                {tooltipInfo.nodeIndex}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Hash Algorithm:
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                {tooltipInfo.hashAlgorithm}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Hash Length:
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                {tooltipInfo.hashLength} bytes ({tooltipInfo.hashLength * 2} hex chars)
              </Typography>
            </Box>
          </Box>

          {tooltipInfo.nodeType === 'leaf' && (
            <>
              <Divider sx={{ my: 1 }} />
              <Typography variant="caption" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                This leaf represents a log entry hash
              </Typography>
            </>
          )}
          {tooltipInfo.nodeType === 'root' && (
            <>
              <Divider sx={{ my: 1 }} />
              <Typography variant="caption" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                This is the Merkle root - signed in checkpoints
              </Typography>
            </>
          )}
        </Box>
      )}
    </div>
  );
}


