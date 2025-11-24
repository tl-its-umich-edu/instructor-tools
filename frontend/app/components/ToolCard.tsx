import React, { useContext, useState } from 'react';
import AddBox from '@mui/icons-material/AddBox';
import { useMutation } from '@tanstack/react-query';
import CheckCircleOutline from '@mui/icons-material/CheckCircleOutline';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  Button, Card, CardActions, CardContent, CardMedia, Collapse, Grid, LinearProgress,
  Tooltip, Typography
} from '@mui/material';

import DataElement from './DataElement';
import ErrorsDisplay from './ErrorsDisplay';
import ImageDialog from './ImageDialog';
import { AddToolButton, RemoveToolButton, LaunchToolButton, TryInternalToolButton } from './toolButtons';
import { updateToolNav } from '../api';
import constants from '../constants';
import { Tool } from '../interfaces';
import { AnalyticsConsentContext } from '../context';
import { useGoogleAnalytics } from '../hooks/useGoogleAnalytics';

const TOOL_IN_MENU_TEXT = `Tool in ${constants.toolMenuName}`;

interface ToolCardProps {
  tool: Tool
  onToolUpdate: (tool: Tool) => void;
}
interface ToolCardAnalyticsParams {
  tool_name: string;
  tool_canvas_id: number;
}

export default function ToolCard (props: ToolCardProps) {
  const { tool, onToolUpdate } = props;

  // ToolCard action handlers with google analytics tracking
  const analyticsConsentContext = useContext(AnalyticsConsentContext);
  const { sendAnalyticsEvent } = useGoogleAnalytics<ToolCardAnalyticsParams>(analyticsConsentContext);
  const handleMoreInfoClick = async (tool: Tool) => {
    try {
      if (!showMoreInfo) { // On opening more info
        sendAnalyticsEvent('More Info Clicked', {
          tool_name: tool.name,
          tool_canvas_id: tool.canvas_id,
        });
      }
      setShowMoreInfo(!showMoreInfo);
    } catch (error) {
      console.error('Error handling more info click:', error);
    }
  };
  const handleLaunchClick = async (tool: Tool) => {
    try {
      sendAnalyticsEvent('Launch Tool', {
        tool_name: tool.name,
        tool_canvas_id: tool.canvas_id,
      });
      window.open(tool.launch_url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.error('Error opening tool launch URL:', error);
    }
  };
  const handleUpdateToolNav = async (tool: Tool, navEnabled: boolean) => {
    try {
      if (navEnabled) {
        sendAnalyticsEvent('Add Tool to Navigation',{
          tool_name: tool.name,
          tool_canvas_id: tool.canvas_id
        });
      } else {
        sendAnalyticsEvent('Remove Tool from Navigation',{
          tool_name: tool.name,
          tool_canvas_id: tool.canvas_id
        });
      }
      doUpdateToolNav({ canvasToolId: tool.canvas_id, navEnabled });
    } catch (error) {
      console.error('Error updating tool navigation:', error);
    }
  };
        

  const [showMoreInfo, setShowMoreInfo] = useState(false);
  const [screenshotDialogOpen, setScreenshotDialogOpen] = useState(false);

  const {
    mutate: doUpdateToolNav, error: updateToolNavError, isPending: updateToolNavPending
  } = useMutation(updateToolNav, { onSuccess: (data, variables) => {
    const newTool = { ...tool, navigation_enabled: variables.navEnabled };
    onToolUpdate(newTool);
  }});

  const moreOrLessText = !showMoreInfo ? 'More' : 'Less';
  const buttonLoadingId = `add-remove-tool-button-loading-${tool.canvas_id}`;

  const isLoading = updateToolNavPending;
  const errors = [updateToolNavError].filter(e => e !== null) as Error[];

  let feedbackBlock;
  if (isLoading || errors.length > 0) {
    feedbackBlock = (
      <CardContent>
        {isLoading && <LinearProgress id={buttonLoadingId} sx={{ margin: 2 }} />}
        {errors.length > 0 && <ErrorsDisplay errors={errors} />}
      </CardContent>
    );
  }

  let mainImageBlock;
  if (tool.main_image !== null) {
    const defaultMainImageAltText = `Image of ${tool.name} tool in use`;
    mainImageBlock = (
      <>
        <Button sx={{ marginBottom: 1 }} onClick={() => setScreenshotDialogOpen(true)}>
          <Grid container direction='column'>
            <Grid item>
              <CardMedia
                component='img'
                height={150}
                alt={tool.main_image_alt_text ?? defaultMainImageAltText}
                image={tool.main_image ?? ''}
                sx={{ marginBottom: 2, objectFit: 'contain' }}
              />
            </Grid>
            <Grid item container alignItems='center'>
              <Grid item>
                <AddBox fontSize='small' sx={{ display: 'inherit', marginRight: 1 }} />
              </Grid>
              <Grid item>
                <Typography variant='inherit'>Enlarge Screenshot</Typography>
              </Grid>
            </Grid>
          </Grid>
        </Button>
        <ImageDialog
          titleData={{ title: `Screenshot for ${tool.name}`, id: `main-image-dialog-title-${tool.canvas_id}` }}
          imageData={{ src: tool.main_image, altText: defaultMainImageAltText }}
          open={screenshotDialogOpen}
          onClose={() => setScreenshotDialogOpen(false)}
        />
      </>
    );
  }

  return (
    <Card
      id={`${tool.name}-tool-${tool.canvas_id}`}
      variant='outlined'
      sx={{ padding: 1, width: 328, borderColor: 'primary.main', borderWidth: '3px' }}
    >
      <CardContent sx={{ height: 260 }}>
        <CardMedia
          component='img'
          height={150}
          alt={tool.logo_image_alt_text ?? `Logo image for ${tool.name} tool`}
          image={tool.logo_image ?? ''}
          sx={{ marginBottom: 2, objectFit: 'contain' }}
        />
        <Typography variant='subtitle1' component='h3' gutterBottom>
          <strong>{tool.name}</strong>
        </Typography>
        <Typography variant='body2'>
          <span dangerouslySetInnerHTML={{ __html: tool.short_description }} />
        </Typography>
      </CardContent>
      {feedbackBlock}
      <CardActions>
        <Grid
          container
          justifyContent='space-between'
          alignItems='center'
          aria-describedby={buttonLoadingId}
          aria-busy={updateToolNavPending}
        >
          <Button
            onClick={() => handleMoreInfoClick(tool)}
            aria-expanded={showMoreInfo}
            aria-label={`Show ${moreOrLessText} Info`}
            startIcon={!showMoreInfo ? <ExpandMoreIcon /> : <ExpandLessIcon />}
          >
            {moreOrLessText}
          </Button>
          {
            tool.launch_url != null
              ? (
                (tool.launch_url.indexOf('://') > 0 || tool.launch_url.indexOf('//') === 0) 
                  ? ( // Absolute Redirect URL (External tool)
                    <LaunchToolButton
                      onClick={() => handleLaunchClick(tool)}
                    />
                  ) : ( // Relative Redirect URL (Internal tool)
                    <TryInternalToolButton
                      url={tool.launch_url}
                    />
                  )
              ) : (
                tool.navigation_enabled
                  ? (
                    <RemoveToolButton
                      disabled={updateToolNavPending}
                      onClick={() => handleUpdateToolNav(tool, false)}
                    />
                  )
                  : (
                    <AddToolButton
                      disabled={updateToolNavPending}
                      onClick={() => handleUpdateToolNav(tool, true)}
                    />
                  )
              )
          }
          {
            tool.navigation_enabled && (
              <Tooltip placement='top' title={TOOL_IN_MENU_TEXT}>
                <CheckCircleOutline
                  color='success'
                  tabIndex={0}
                  aria-label={TOOL_IN_MENU_TEXT}
                  role='button'
                  aria-hidden={false}
                  focusable
                />
              </Tooltip>
            )
          }
        </Grid>
      </CardActions>
      <Collapse in={showMoreInfo} unmountOnExit>
        <CardContent>
          <DataElement name='Description'>
            <span dangerouslySetInnerHTML={{ __html: tool.long_description }} />
          </DataElement>
          {mainImageBlock}
          <DataElement name='Privacy Agreement'>
            <span dangerouslySetInnerHTML={{ __html: tool.privacy_agreement }} />
          </DataElement>
          {tool.canvas_placement_expanded.length > 0 && (
            <DataElement name='Placements'>
              {tool.canvas_placement_expanded.map(p => p.name).join(', ')}
            </DataElement>
          )}
          {tool.tool_categories_expanded.length > 0 && (
            <DataElement name='Categories'>
              {tool.tool_categories_expanded.map(p=> p.category_name).join(', ')}
            </DataElement>
          )}
          <DataElement name='Support Resources'>
            <span dangerouslySetInnerHTML={{ __html: tool.support_resources }} />
          </DataElement>
        </CardContent>
      </Collapse>
    </Card>
  );
}
