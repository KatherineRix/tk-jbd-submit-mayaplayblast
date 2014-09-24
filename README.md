tk-submit_mayaplayblast
=====================

Application to playblast assets or shots.

Dep:
https://github.com/shotgunsoftware/python-api


INSTALL NOTES:

1. You must have the python-api installed for shotgun!
2. You must uncomment and change the lines in the app.py file to be the correct information for your shotgun setup!

        #base_url    = #[INSERT YOUR URL HERE eg https://mystudio.shotgunstudio.com AS A STRING]
        #script_name = #[INSERT YOUR SCRIPTNAME] eg Toolkit
        #api_key     = #[INSERT YOUR API KEY HERE] eg 724eea86a7hhhe4816b8f24833112eacf42834a2b5cb85f814f125e96078a3b3

    eg:

        base_url    = "https://mystudio.shotgunstudio.com"
        script_name = "Toolkit"
        api_key     = "724eea86a7hhhe4816b8f24833112eacf42834a2b5cb85f814f125e96078a3b3"

3. Adding to the asset_step and shot_step:

      tk-submit-maya-shotPlayblast:

            location:                   {name: tk-jbd-submit-mayaplayblast, type: dev, path: 'path/to/install/directory'}
            display_name:               .Publish TurnTable For Review...
            cameraSuffix:               _shotCam
            isAsset:                    true
            movie_width:                1280
            movie_height:               720
            movie_path_template:        maya_asset_playblast
            movie_workpath_template:    maya_assetwork_playblast
            new_version_status:         rev
            sg_in_frame_field:          sg_cut_in
            sg_out_frame_field:         sg_cut_out
            store_on_disk:              true
            template_work:              maya_asset_work
            upload_to_shotgun:          true
            version_number_padding:     3

NOTE: it is important to note using dev path will cause some cross platform issues because you'll end up with a hard coded path here
To avoid this you can copy the application into the studio/install/apps/app_store/ directory and use:

        type: app_store, version: v0.0.1

HOW EVER! This will cause tank updates to fail because the applications don't exist in the offical appstore, so before doing a
tank updates you'll need to remove or change these paths back to dev.

<br>
<center>
<img src = "http://www.anim83d.com/images/github/mpb_01.PNG"><br>
<img src = "http://www.anim83d.com/images/github/mpb_02.PNG"><br>
More to come...
</center>