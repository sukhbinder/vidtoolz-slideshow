import vidtoolz
import os
import subprocess
import json
from PIL import Image

def parse_image_list(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_image_size(image_path):
    with Image.open(image_path) as img:
        return img.width, img.height

def make_even(x):
    return x if x % 2 == 0 else x + 1

def group_images_by_resolution(image_paths):
    groups = {}
    for img_path in image_paths:
        if not os.path.isfile(img_path):
            continue
        try:
            width, height = get_image_size(img_path)
            key = f"{width}x{height}"
            groups.setdefault(key, []).append(img_path)
        except Exception as e:
            print(f"Failed to read image size: {img_path} — {e}")
    return groups

def generate_clip(image_path, output_path, resolution, duration, fade_duration, skip_padding=False):
    target_width, target_height = map(int, resolution.split("x"))

    fade_in = fade_duration
    fade_out = fade_duration
    fade_out_start = duration - fade_out

    if skip_padding:
        filter_str = (
            f"format=yuv420p,"
            f"fade=t=in:st=0:d={fade_in},"
            f"fade=t=out:st={fade_out_start}:d={fade_out},"
            f"scale=trunc(iw/2)*2:trunc(ih/2)*2,"
            f"fps=30"
        )
    else:
        img_width, img_height = get_image_size(image_path)
        canvas_width = make_even(max(target_width, img_width))
        canvas_height = make_even(max(target_height, img_height))

        filter_str = (
            f"scale=w={canvas_width}:h={canvas_height}:force_original_aspect_ratio=decrease,"
            f"pad={canvas_width}:{canvas_height}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"scale=trunc(iw/2)*2:trunc(ih/2)*2,"
            f"format=yuv420p,"
            f"fade=t=in:st=0:d={fade_in},"
            f"fade=t=out:st={fade_out_start}:d={fade_out},"
            f"fps=30"
        )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-t", str(duration),
        "-i", image_path,
        "-vf", filter_str,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        output_path
    ]

    subprocess.run(cmd, check=True)

def create_video_from_clips(clips, output_path):
    list_file = "temp_clip_list.txt"
    with open(list_file, 'w') as f:
        for clip in clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    subprocess.run(cmd, check=True)
    os.remove(list_file)

def process_group(resolution, images, output_dir, duration, fade):
    temp_dir = os.path.join(output_dir, "temp_clips")
    os.makedirs(temp_dir, exist_ok=True)
    output_video = os.path.join(output_dir, f"{resolution}.mp4")

    clips = []
    for idx, image in enumerate(images):
        clip_path = os.path.join(temp_dir, f"clip_{idx:03d}.mp4")
        skip_padding = len(images) == 1
        generate_clip(image, clip_path, resolution, duration, fade, skip_padding)
        clips.append(clip_path)

    create_video_from_clips(clips, output_video)

def create_parser(subparser):
    parser = subparser.add_parser("slideshow", description="Create slideshow with images using ffmpeg")
    # Add subprser arguments here.
    parser.add_argument("image_list", help="Path to text file containing list of image paths (ordered)")
    parser.add_argument("-o","--output_dir", default="slideshows", help="Directory to save slideshows")
    parser.add_argument("-d","--duration", type=float, default=3.0, help="Duration per image (seconds)")
    parser.add_argument("-f","--fade", type=float, default=0.5, help="Fade in/out duration (seconds)")
    return parser


class ViztoolzPlugin:
    """ Create slideshow with images using ffmpeg """
    __name__ = "slideshow"

    @vidtoolz.hookimpl
    def register_commands(self, subparser):
        self.parser = create_parser(subparser)
        self.parser.set_defaults(func=self.run)

    def run(self, args):
        # add actual call here

        folderpath = os.path.dirname(args.image_list)
        if folderpath:
            cwd = os.getcwd()
            os.chdir(folderpath)
        else:
            cwd = None

        os.makedirs(args.output_dir, exist_ok=True)
        images = parse_image_list(os.path.basename(args.image_list))
        grouped = group_images_by_resolution(images)

        # Save groups to JSON (optional metadata)
        with open(os.path.join(args.output_dir, "groups.json"), "w") as f:
            json.dump(grouped, f, indent=2)

        for resolution, imgs in grouped.items():
            print(f"Processing group: {resolution} with {len(imgs)} image(s)")
            process_group(resolution, imgs, args.output_dir, args.duration, args.fade)
        if cwd:
            os.chdir(cwd)
    def hello(self, args):
        # this routine will be called when "vidtoolz "slideshow is called."
        print("Hello! This is an example ``vidtoolz`` plugin.")

slideshow_plugin = ViztoolzPlugin()
