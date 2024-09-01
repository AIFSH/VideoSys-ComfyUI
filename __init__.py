import os,sys
now_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(now_dir)
import time
import folder_paths
from videosys import CogVideoXConfig,VideoSysEngine,LatteConfig,OpenSoraConfig,OpenSoraPlanConfig

output_dir = folder_paths.get_output_directory()

class TextNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"text": ("STRING", {"multiline": True, "dynamicPrompts": True}),}}
    RETURN_TYPES = ("TEXT",)
    FUNCTION = "encode"

    CATEGORY = "AIFSH_VideoSys"

    def encode(self, text):
        return (text, )

class PreViewVideo:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":{
            "video":("VIDEO",),
        }}
    
    CATEGORY = "AIFSH_VideoSys"
    DESCRIPTION = "hello world!"

    RETURN_TYPES = ()

    OUTPUT_NODE = True

    FUNCTION = "load_video"

    def load_video(self, video):
        video_name = os.path.basename(video)
        video_path_name = os.path.basename(os.path.dirname(video))
        return {"ui":{"video":[video_name,video_path_name]}}

class VideoSysNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required":{
                "prompt":("TEXT",),
                "mode":(["base","pab","low_mem"],),
                "model_name":(["THUDM/CogVideoX-2b",
                               "THUDM/CogVideoX-5b",
                               "maxin-cn/Latte-1",
                               "OpenSora",
                               "OpenSoraPlan"],),
                "num_frames":([65,221],{
                    "default":65
                }),
                "guidance_scale":("FLOAT",{
                    "default":6.
                }),
                "num_inference_steps":("INT",{
                    "default":50
                }),
            }
        }
    
    RETURN_TYPES = ("VIDEO",)
    #RETURN_NAMES = ("image_output_name",)

    FUNCTION = "gen_video"

    #OUTPUT_NODE = False

    CATEGORY = "AIFSH_VideoSys"

    def gen_video(self,prompt,mode,model_name,
                  num_frames,guidance_scale,num_inference_steps):
        if "CogVideoX" in model_name:
            config = CogVideoXConfig(model_path=model_name,
                                     enable_pab=True if mode=="pab" else False,
                                     cpu_offload=True if mode=="low_mem" else False,
                                     vae_tiling=True if mode=="low_mem" else False)
            engine = VideoSysEngine(config)

            video = engine.generate(
                prompt=prompt,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                num_frames = 49 if num_frames > 49 else num_frames
            ).video[0]
            model_name = model_name.split("/")[-1]

        elif "Latte" in model_name:
            config = LatteConfig(model_path=model_name,
                                 enable_pab=True if mode=="pab" else False,)
            engine = VideoSysEngine(config)
            video = engine.generate(
                prompt=prompt,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
            ).video[0]
            model_name = model_name.split("/")[-1]

        elif model_name == "OpenSora":
            config = OpenSoraConfig(num_sampling_steps=num_inference_steps,
                                    cfg_scale=guidance_scale,
                                    enable_pab=True if mode=="pab" else False)
            
            engine = VideoSysEngine(config)
            # num frames: 2s, 4s, 8s, 16s
            # resolution: 144p, 240p, 360p, 480p, 720p
            # aspect ratio: 9:16, 16:9, 3:4, 4:3, 1:1
            video = engine.generate(
                prompt=prompt,
                resolution="480p",
                aspect_ratio="9:16",
                num_frames="2s",
            ).video[0]
        else:
            config = OpenSoraPlanConfig(num_frames=num_frames,
                                        enable_pab=True if mode=="pab" else False)
            engine = VideoSysEngine(config)
            video = engine.generate(
                prompt=prompt,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
            ).video[0]
        
        video_path = os.path.join(output_dir,f"{model_name}_{mode}_{time.time_ns()}.mp4")
        engine.save_video(video, video_path)

        return (video_path,)

# Set the web directory, any .js file in that directory will be loaded by the frontend as a frontend extension
WEB_DIRECTORY = "./web"

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "TextNode": TextNode,
    "PreViewVideo":PreViewVideo,
    "VideoSysNode":VideoSysNode
}