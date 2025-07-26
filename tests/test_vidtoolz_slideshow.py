import pytest
from unittest.mock import MagicMock, patch, call
from argparse import ArgumentParser
import os
from PIL import Image

import vidtoolz_slideshow as w

@pytest.fixture
def runner(tmp_path):
    """Provides a temporary directory for test artifacts."""
    return tmp_path

def create_dummy_image(path, width=100, height=100):
    """Creates a dummy image file."""
    img = Image.new('RGB', (width, height), color = 'red')
    img.save(path)

def test_parse_image_list(runner):
    """Tests the parse_image_list function."""
    image_list_path = runner / "image_list.txt"
    
    # Test with a valid file
    with open(image_list_path, 'w') as f:
        f.write("img1.jpg\nimg2.png\n")
    assert w.parse_image_list(image_list_path) == ["img1.jpg", "img2.png"]

    # Test with a file with empty lines
    with open(image_list_path, 'w') as f:
        f.write("img1.jpg\n\nimg2.png\n")
    assert w.parse_image_list(image_list_path) == ["img1.jpg", "img2.png"]

    # Test with an empty file
    with open(image_list_path, 'w') as f:
        f.write("")
    assert w.parse_image_list(image_list_path) == []

def test_get_image_size(runner):
    """Tests the get_image_size function."""
    img_path = runner / "test.jpg"
    create_dummy_image(img_path, 150, 200)
    assert w.get_image_size(img_path) == (150, 200)

def test_make_even():
    """Tests the make_even function."""
    assert w.make_even(10) == 10
    assert w.make_even(11) == 12

def test_group_images_by_resolution(runner):
    """Tests the group_images_by_resolution function."""
    img1 = runner / "img1.jpg"
    img2 = runner / "img2.jpg"
    img3 = runner / "img3.png"
    
    create_dummy_image(img1, 100, 100)
    create_dummy_image(img2, 200, 200)
    create_dummy_image(img3, 100, 100)

    image_paths = [str(img1), str(img2), str(img3), "non_existent.jpg"]
    
    groups = w.group_images_by_resolution(image_paths)
    
    assert "100x100" in groups
    assert "200x200" in groups
    assert groups["100x100"] == [str(img1), str(img3)]
    assert groups["200x200"] == [str(img2)]

@patch('subprocess.run')
def test_generate_clip(mock_run, runner):
    """Tests the generate_clip function."""
    img_path = runner / "test.jpg"
    create_dummy_image(img_path, 100, 100)
    output_path = runner / "clip.mp4"
    
    # Test with padding
    w.generate_clip(str(img_path), str(output_path), "200x200", 3.0, 0.5)
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "pad=200:200" in args[0][9]

    mock_run.reset_mock()

    # Test with skip_padding
    w.generate_clip(str(img_path), str(output_path), "100x100", 3.0, 0.5, skip_padding=True)
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "pad" not in args[0][9]

@patch('os.remove')
@patch('subprocess.run')
def test_create_video_from_clips(mock_run, mock_remove, runner):
    """Tests the create_video_from_clips function."""
    clips = [str(runner / "clip1.mp4"), str(runner / "clip2.mp4")]
    output_path = runner / "video.mp4"
    
    w.create_video_from_clips(clips, str(output_path))
    
    mock_run.assert_called_once()
    # Check that the temp file is removed
    mock_remove.assert_called_once_with("temp_clip_list.txt")

@patch('vidtoolz_slideshow.generate_clip')
@patch('vidtoolz_slideshow.create_video_from_clips')
def test_process_group(mock_create_video, mock_generate_clip, runner):
    """Tests the process_group function."""
    images = [str(runner / "img1.jpg"), str(runner / "img2.jpg")]
    output_dir = runner / "output"
    
    w.process_group("100x100", images, str(output_dir), 3.0, 0.5)
    
    assert mock_generate_clip.call_count == 2
    mock_create_video.assert_called_once()

def test_create_parser():
    """Tests the create_parser function."""
    subparser = ArgumentParser().add_subparsers()
    parser = w.create_parser(subparser)
    
    args = parser.parse_args([
        "my_images.txt",
        "--output_dir", "my_slideshows",
        "--duration", "5.0",
        "--fade", "1.0"
    ])
    
    assert args.image_list == "my_images.txt"
    assert args.output_dir == "my_slideshows"
    assert args.duration == 5.0
    assert args.fade == 1.0

@patch('vidtoolz_slideshow.process_group')
@patch('vidtoolz_slideshow.group_images_by_resolution', return_value={"100x100": ["img1.jpg"]})
@patch('vidtoolz_slideshow.parse_image_list', return_value=["img1.jpg"])
def test_viztoolz_plugin_run(mock_parse, mock_group, mock_process, runner):
    """Tests the run method of the ViztoolzPlugin."""
    plugin = w.ViztoolzPlugin()
    args = MagicMock()
    output_dir = runner / "slideshows"
    args.output_dir = str(output_dir)
    args.image_list = "images.txt"
    args.duration = 3.0
    args.fade = 0.5
    
    plugin.run(args)
    
    mock_parse.assert_called_once_with("images.txt")
    mock_group.assert_called_once_with(["img1.jpg"])
    mock_process.assert_called_once_with("100x100", ["img1.jpg"], str(output_dir), 3.0, 0.5)
    assert (output_dir / "groups.json").is_file()

def test_register_commands():
    """Tests the register_commands method."""
    plugin = w.ViztoolzPlugin()
    subparser = MagicMock()
    parser = MagicMock()
    subparser.add_parser.return_value = parser
    
    plugin.register_commands(subparser)
    
    subparser.add_parser.assert_called_once_with("slideshow", description=plugin.__doc__)
    parser.set_defaults.assert_called_once_with(func=plugin.run)