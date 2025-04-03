import React, { useState } from 'react';
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
import { AddToolButton, RemoveToolButton } from './toolButtons';
import { updateToolNav } from '../api';
import constants from '../constants';
import { Tool } from '../interfaces';

const TOOL_IN_MENU_TEXT = `Tool in ${constants.toolMenuName}`;

interface ToolCardProps {
  tool: Tool
  onToolUpdate: (tool: Tool) => void;
}

export default function ToolCard (props: ToolCardProps) {
  const { tool, onToolUpdate } = props;

  const [showMoreInfo, setShowMoreInfo] = useState(false);
  const [screenshotDialogOpen, setScreenshotDialogOpen] = useState(false);

  const {
    mutate: doUpdateToolNav, error: updateToolNavError, isLoading: updateToolNavLoading
  } = useMutation(updateToolNav, { onSuccess: (data, variables) => {
    const newTool = { ...tool, navigation_enabled: variables.navEnabled };
    onToolUpdate(newTool);
  }});

  const moreOrLessText = !showMoreInfo ? 'More' : 'Less';
  const buttonLoadingId = `add-remove-tool-button-loading-${tool.canvas_id}`;

  const isLoading = updateToolNavLoading;
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
          aria-busy={updateToolNavLoading}
        >
          <Button
            onClick={() => setShowMoreInfo(!showMoreInfo)}
            aria-expanded={showMoreInfo}
            aria-label={`Show ${moreOrLessText} Info`}
            startIcon={!showMoreInfo ? <ExpandMoreIcon /> : <ExpandLessIcon />}
          >
            {moreOrLessText}
          </Button>
          <Button
            href={tool.sessionless_launch_url}
            target='_blank'
            aria-label={`Launch ${tool.name} tool`}
            variant='contained'>
              Launch
          </Button>

          {
            tool.navigation_enabled
              ? (
                <RemoveToolButton
                  disabled={updateToolNavLoading}
                  onClick={() => doUpdateToolNav({ canvasToolId: tool.canvas_id, navEnabled: false })}
                />
              )
              : (
                <AddToolButton
                  disabled={updateToolNavLoading}
                  onClick={() => doUpdateToolNav({ canvasToolId: tool.canvas_id, navEnabled: true })}
                />
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
          <DataElement name='Placements'>
            {tool.canvas_placement_expanded.map(p => p.name).join(', ')}
          </DataElement>
          <DataElement name='Support Resources'>
            <span dangerouslySetInnerHTML={{ __html: tool.support_resources }} />
          </DataElement>
        </CardContent>
      </Collapse>
    </Card>
  );
}
