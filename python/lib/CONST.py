"""
Created by James Dunlop
This is if you are using your own config and wish to add this application to it.
It is mainly used for the api to set the base paths from and the debugging for the tool.
"""
#############################################
## CONFIG CONSTANTS
#############################################
DEBUGGING            = True
### The following set the options that will show up for the artists to set.
CAM_SETTINGS_OPTIONS = ['NURBS Curves',
                        'NURBS Surfaces',
                        'Polygons',
                        'Subdiv Surfaces',
                        'Planes',
                        'Lights',
                        'Cameras',
                        'Joints',
                        'IK Handles',
                        'Deformers',
                        'Dynamics',
                        'Fluids',
                        'nParticles',
                        'nRigids',
                        'Dynamic Constraints',
                        'Locators',
                        'Dimensions',
                        'Pivots',
                        'Handles',
                        'Texture Placements',
                        'Strokes',
                        'Motion Trails',
                        'Plugin Shapes',
                        'Manipulators',
                        'Clip Ghosts',
                        'GPU Caches',
                        'Nurbs CVs',
                        'NURBS Hulls',
                        'Grid',
                        'HUD',
                        'Image Planes'
                        ]
### The following set the default cam options to on you can copy and paste from the list above to turn any of them on by default.
CAM_SETTINGS_DEFAULT_ON = ['Polygons',
                            'HUD',
                            'NURBS Surfaces',
                            'GPU Caches',
                            'Plugin Shapes',
                            'Image Planes',
                            'NURBS Curves'
                            ]

### The following set the options that will show up for the artists to set for the viewport shading options.
VIEWPORT_SETTINGS_OPTIONS = ['WireFrame',
                             'SmoothShade All',
                             'Bounding Box',
                             'Use Default Mat',
                             'X-Ray',
                             'X-Ray Joints',
                             'Hardware Texturing',
                             'Wireframe on Shaded'
                            ]
### The following set the default cam options to on you can copy and paste from the list above to turn any of them on by default.
VIEWPORT_SETTINGS_DEFAULT_ON = ['SmoothShade All',
                                ]
### The following set the options that will show up for the artists to set for the choice of viewport renderer.
RENDERER_SETTINGS_OPTIONS = ['Default Renderer',
                             'Viewport 2.0'
                            ]
### The following set the default cam options to on you can copy and paste from the list above to turn any of them on by default.
RENDERER_SETTINGS_DEFAULT_ON = ['Default Renderer']

## The below settings mainly correspond to the cmds.playblast options used by the app to perform the playblast
PB_FORMAT               = 'qt'
PB_COMPRESSION          = 'h.264'
PB_OFFSCREEN            = True
PB_ACTIVEEDITOR         = False
PB_CLEARCACHE           = False
PB_COMBINESOUND         = True
PB_FORCEOVERWRITE       = True
PB_FRAMEPADDING         = 4
PB_OPTIONS              = False
PB_SEQUENCETIME         = False
PB_SHOWORNAMENTS        = True
PB_VIEWER               = True

SHOTCAM_SUFFIX          = 'shotCam'