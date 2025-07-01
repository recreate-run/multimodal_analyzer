#!/usr/bin/env python3
"""
Example usage patterns for the Media Analyzer CLI with audio analysis.

This script demonstrates various ways to use the media-analyzer CLI for audio content.
"""

import os
import subprocess
from pathlib import Path


def run_command(cmd: list[str], description: str) -> None:
    """Run a CLI command and display the output."""
    print(f"\n{'='*60}")
    print(f"Example: {description}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("Output:")
            print(result.stdout)
        else:
            print("Error:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("Command timed out after 5 minutes")
    except Exception as e:
        print(f"Error running command: {e}")


def main():
    """Run audio analysis examples."""

    print("Media Analyzer CLI - Audio Analysis Examples")
    print("=" * 60)

    # Set environment variables (you should set these with your actual API keys)
    example_env = {
        "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
        "AZURE_OPENAI_KEY": "your-azure-openai-key",
        "GEMINI_API_KEY": "your-gemini-api-key",
        "OPENAI_API_KEY": "your-openai-key",
    }

    print("Required Environment Variables:")
    for key, value in example_env.items():
        print(f"  {key}={value}")
    print(
        "\nPlease set these environment variables with your actual API keys before running."
    )

    # Audio file paths (replace with actual audio files)
    audio_file = "path/to/your/audio.mp3"
    video_file = "path/to/your/video.mp4"
    audio_directory = "path/to/audio/files/"

    print(f"\nNote: Replace file paths with actual audio/video files:")
    print(f"  Audio file: {audio_file}")
    print(f"  Video file: {video_file}")
    print(f"  Audio directory: {audio_directory}")

    # Example 1: Basic audio transcription
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            audio_file,
            "--audio-mode",
            "transcript",
            "--model",
            "whisper-1",
        ],
        "Basic audio transcription",
    )

    # Example 2: Audio transcription with verbose output
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            audio_file,
            "--audio-mode",
            "transcript",
            "--model",
            "whisper-1",
            "--verbose",
            "--output",
            "markdown",
        ],
        "Audio transcription with verbose markdown output",
    )

    # Example 3: Audio analysis (description mode)
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            audio_file,
            "--audio-mode",
            "description",
            "--model",
            "gpt-4o-mini",
            "--word-count",
            "200",
        ],
        "Audio content analysis with GPT-4",
    )

    # Example 4: Video audio extraction and analysis
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            video_file,
            "--audio-mode",
            "description",
            "--model",
            "gemini/gemini-2.5-flash",
            "--prompt",
            "Summarize the key points discussed in this video",
            "--output",
            "text",
        ],
        "Video audio extraction and analysis",
    )

    # Example 5: Custom prompt for specific analysis
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            audio_file,
            "--audio-mode",
            "description",
            "--model",
            "claude-3-sonnet-20240229",
            "--prompt",
            "Analyze the sentiment and emotional tone of this audio content",
            "--word-count",
            "150",
        ],
        "Sentiment analysis with custom prompt",
    )

    # Example 6: Batch processing audio directory
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            audio_directory,
            "--audio-mode",
            "transcript",
            "--model",
            "whisper-1",
            "--recursive",
            "--concurrency",
            "2",
            "--output",
            "json",
            "--output-file",
            "batch_transcripts.json",
        ],
        "Batch transcription of audio directory",
    )

    # Example 7: Meeting transcription and analysis
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            audio_file,
            "--audio-mode",
            "description",
            "--model",
            "gpt-4o-mini",
            "--prompt",
            "Analyze this meeting recording and identify key decisions, action items, and main discussion points",
            "--word-count",
            "300",
            "--output",
            "markdown",
            "--output-file",
            "meeting_analysis.md",
            "--verbose",
        ],
        "Meeting recording analysis",
    )

    # Example 8: Podcast analysis
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            audio_file,
            "--audio-mode",
            "description",
            "--model",
            "gemini/gemini-2.5-flash",
            "--prompt",
            "Summarize this podcast episode, highlighting main topics, guest insights, and key takeaways",
            "--word-count",
            "250",
            "--output",
            "text",
        ],
        "Podcast episode analysis",
    )

    # Example 9: Azure OpenAI with specific endpoint
    print("\nExample 9: Using Azure OpenAI")
    print("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY environment variables")
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            audio_file,
            "--audio-mode",
            "description",
            "--model",
            "gpt-4o-mini",  # Azure OpenAI model
            "--word-count",
            "200",
        ],
        "Analysis using Azure OpenAI",
    )

    # Example 10: Error handling demonstration
    run_command(
        [
            "uv",
            "run",
            "media-analyzer",
            "--type",
            "audio",
            "--path",
            "nonexistent_file.mp3",
            "--audio-mode",
            "transcript",
            "--model",
            "whisper-1",
        ],
        "Error handling for non-existent file",
    )

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("Note: These examples use placeholder file paths.")
    print("Replace with actual audio/video files and set your API keys to test.")


if __name__ == "__main__":
    main()
