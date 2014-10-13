tk-submit_mayaplayblast
=====================
###Description:

Application to playblast assets or shots.

####Dependencies:<br>
**https://github.com/shotgunsoftware/python-api**
<br>
####General application notes:<br>
It is important to note using dev path will cause some **cross platform** issues because you'll end up with a hard coded path.<br>
To avoid this you can copy the application into the studio/install/apps/app_store/ directory and use:<br>
`location: {name: tk-jbd-submit-mayaplayblast, type: app_store, version: v0.0.1}`<br>
**HOW EVER!**<br>
*__This will cause tank updates to fail because the applications don't exist in the official app store__*<br>
So before doing a tank update you'll need to remove or change these paths back to dev!<br>
<br>
<hr>
#APPLICATION INSTALL NOTES:
please refer to manual install location from docs here:
https://toolkit.shotgunsoftware.com/entries/23797786#Apps%20in%20git%20%28and%20github%29
I have found this to be the most reliable for cross platform install locations

* **You must have the python-api installed for shotgun!**
* Adding to the asset_step and shot_step:
```
      tk-submit-maya-shotPlayblast:

            location:                   {"type": "manual", "name": "tk-jbd-submit-mayaplayblast", "version": "v0.0.1"}
            display_name:               .Publish TurnTable For Review...
            showOptions:                true
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
```
It is important to note here if you wish to expose the options for the playblast like in the images below use the value true in the showOptions. If you wish to just
set some defaults and not have the artists change these use the CONST file to set the default on options and set the showOptions to false.

<br>
<center>
<img src = "http://www.anim83d.com/images/github/mpb_01.PNG"><br>
<img src = "http://www.anim83d.com/images/github/mpb_02.PNG"><br>
More to come...
</center>