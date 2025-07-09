import json
from datetime import datetime
from pathlib import Path
from typing import Any


class OutputFormatter:
    """Handles different output formats for analysis results."""
    
    @staticmethod
    def format_json(results: list[dict[str, Any]], pretty: bool = True, verbose: bool = False) -> str:
        """Format results as JSON."""
        if not verbose:
            # Non-verbose mode: only image path and analysis result
            simplified_results = []
            for result in results:
                simplified = {
                    "image_path": result.get("image_path"),
                    "analysis": result.get("analysis") if result.get("success") else None,
                    "success": result.get("success", False)
                }
                if not result.get("success"):
                    simplified["error"] = result.get("error")
                simplified_results.append(simplified)
            results = simplified_results
        
        if pretty:
            return json.dumps(results, indent=2, ensure_ascii=False)
        return json.dumps(results, ensure_ascii=False)
    
    @staticmethod
    def format_markdown(results: list[dict[str, Any]], verbose: bool = False) -> str:
        """Format results as Markdown."""
        if not results:
            return "# Image Analysis Results\n\nNo results found."
        
        md_content = ["# Image Analysis Results\n"]
        if verbose:
            md_content.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            md_content.append(f"**Total Images:** {len(results)}\n")
        
        for i, result in enumerate(results, 1):
            md_content.append(f"## Image {i}: {Path(result['image_path']).name}\n")
            md_content.append(f"**Path:** `{result['image_path']}`\n")
            
            if verbose:
                md_content.append(f"**Model:** {result.get('model', 'unknown')}\n")
                if result.get("prompt"):
                    md_content.append(f"**Prompt:** {result['prompt']}\n")
                if result.get("word_count"):
                    md_content.append(f"**Word Count:** {result['word_count']}\n")
            
            if result["success"]:
                md_content.append("**Analysis:**\n")
                md_content.append(f"{result['analysis']}\n")
            else:
                md_content.append(f"**Error:** {result['error']}\n")
            
            md_content.append("---\n")
        
        return "\n".join(md_content)
    
    @staticmethod
    def format_text(results: list[dict[str, Any]], verbose: bool = False) -> str:
        """Format results as plain text."""
        if not results:
            return "Image Analysis Results\n\nNo results found."
        
        text_content = ["Image Analysis Results"]
        text_content.append("=" * 50)
        
        if verbose:
            text_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            text_content.append(f"Total Images: {len(results)}")
            text_content.append("")
        
        for i, result in enumerate(results, 1):
            text_content.append(f"Image {i}: {Path(result['image_path']).name}")
            text_content.append(f"Path: {result['image_path']}")
            
            if verbose:
                text_content.append(f"Model: {result.get('model', 'unknown')}")
                if result.get("prompt"):
                    text_content.append(f"Prompt: {result['prompt']}")
                if result.get("word_count"):
                    text_content.append(f"Word Count: {result['word_count']}")
            
            text_content.append("")
            
            if result["success"]:
                text_content.append("Analysis:")
                text_content.append(result["analysis"])
            else:
                text_content.append(f"Error: {result['error']}")
            
            text_content.append("")
            text_content.append("-" * 50)
            text_content.append("")
        
        return "\n".join(text_content)
    
    @staticmethod
    def save_to_file(content: str, file_path: str) -> None:
        """Save content to file."""
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    @staticmethod
    def get_output_extension(format_type: str) -> str:
        """Get appropriate file extension for format."""
        extensions = {
            "json": ".json",
            "markdown": ".md",
            "text": ".txt"
        }
        return extensions.get(format_type, ".txt")
    
    @staticmethod
    def format_audio_json(results: list[dict[str, Any]], pretty: bool = True, verbose: bool = False) -> str:
        """Format audio analysis results as JSON."""
        if not verbose:
            # Non-verbose mode: only audio path and main result
            simplified_results = []
            for result in results:
                mode = result.get("mode", "unknown")
                simplified = {
                    "audio_path": result.get("audio_path"),
                    "mode": mode,
                    "success": result.get("success", False)
                }
                
                if result.get("success"):
                    if mode == "transcript":
                        simplified["transcript"] = result.get("transcript")
                    elif mode == "description":
                        simplified["analysis"] = result.get("analysis")
                        simplified["transcript"] = result.get("transcript")
                else:
                    simplified["error"] = result.get("error")
                    
                simplified_results.append(simplified)
            results = simplified_results
        
        if pretty:
            return json.dumps(results, indent=2, ensure_ascii=False)
        return json.dumps(results, ensure_ascii=False)
    
    @staticmethod
    def format_audio_markdown(results: list[dict[str, Any]], verbose: bool = False) -> str:
        """Format audio analysis results as Markdown."""
        if not results:
            return "# Audio Analysis Results\n\nNo results found."
        
        md_content = ["# Audio Analysis Results\n"]
        if verbose:
            md_content.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            md_content.append(f"**Total Audio Files:** {len(results)}\n")
        
        for i, result in enumerate(results, 1):
            md_content.append(f"## Audio {i}: {Path(result['audio_path']).name}\n")
            md_content.append(f"**Path:** `{result['audio_path']}`\n")
            md_content.append(f"**Mode:** {result.get('mode', 'unknown')}\n")
            
            if verbose and result.get("audio_info"):
                audio_info = result["audio_info"]
                md_content.append(f"**Duration:** {audio_info.get('duration_minutes', 0):.1f} minutes\n")
                md_content.append(f"**Format:** {audio_info.get('format', 'unknown')}\n")
                
            if verbose:
                if result.get("transcription_model"):
                    md_content.append(f"**Transcription Model:** {result['transcription_model']}\n")
                if result.get("analysis_model"):
                    md_content.append(f"**Analysis Model:** {result['analysis_model']}\n")
                if result.get("prompt"):
                    md_content.append(f"**Prompt:** {result['prompt']}\n")
                if result.get("word_count"):
                    md_content.append(f"**Word Count:** {result['word_count']}\n")
            
            if result["success"]:
                if result.get("mode") == "transcript":
                    md_content.append("**Transcript:**\n")
                    md_content.append(f"{result.get('transcript', 'No transcript available')}\n")
                elif result.get("mode") == "description":
                    if verbose:
                        md_content.append("**Transcript:**\n")
                        md_content.append(f"{result.get('transcript', 'No transcript available')}\n\n")
                    md_content.append("**Analysis:**\n")
                    md_content.append(f"{result.get('analysis', 'No analysis available')}\n")
            else:
                md_content.append(f"**Error:** {result.get('error', 'Unknown error')}\n")
            
            md_content.append("---\n")
        
        return "\n".join(md_content)
    
    @staticmethod
    def format_audio_text(results: list[dict[str, Any]], verbose: bool = False) -> str:
        """Format audio analysis results as plain text."""
        if not results:
            return "Audio Analysis Results\n\nNo results found."
        
        text_content = ["Audio Analysis Results"]
        text_content.append("=" * 50)
        
        if verbose:
            text_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            text_content.append(f"Total Audio Files: {len(results)}")
            text_content.append("")
        
        for i, result in enumerate(results, 1):
            text_content.append(f"Audio {i}: {Path(result['audio_path']).name}")
            text_content.append(f"Path: {result['audio_path']}")
            text_content.append(f"Mode: {result.get('mode', 'unknown')}")
            
            if verbose and result.get("audio_info"):
                audio_info = result["audio_info"]
                text_content.append(f"Duration: {audio_info.get('duration_minutes', 0):.1f} minutes")
                text_content.append(f"Format: {audio_info.get('format', 'unknown')}")
                
            if verbose:
                if result.get("transcription_model"):
                    text_content.append(f"Transcription Model: {result['transcription_model']}")
                if result.get("analysis_model"):
                    text_content.append(f"Analysis Model: {result['analysis_model']}")
                if result.get("prompt"):
                    text_content.append(f"Prompt: {result['prompt']}")
                if result.get("word_count"):
                    text_content.append(f"Word Count: {result['word_count']}")
            
            text_content.append("")
            
            if result["success"]:
                if result.get("mode") == "transcript":
                    text_content.append("Transcript:")
                    text_content.append(result.get("transcript", "No transcript available"))
                elif result.get("mode") == "description":
                    if verbose:
                        text_content.append("Transcript:")
                        text_content.append(result.get("transcript", "No transcript available"))
                        text_content.append("")
                    text_content.append("Analysis:")
                    text_content.append(result.get("analysis", "No analysis available"))
            else:
                text_content.append(f"Error: {result.get('error', 'Unknown error')}")
            
            text_content.append("")
            text_content.append("-" * 50)
            text_content.append("")
        
        return "\n".join(text_content)
    
    def format_audio_results(self, results: list[dict[str, Any]], format_type: str, verbose: bool = False) -> str:
        """Format audio analysis results in the specified format."""
        if format_type == "json":
            return self.format_audio_json(results, verbose=verbose)
        elif format_type == "markdown":
            return self.format_audio_markdown(results, verbose=verbose)
        elif format_type == "text":
            return self.format_audio_text(results, verbose=verbose)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    @staticmethod
    def format_video_json(results: list[dict[str, Any]], pretty: bool = True, verbose: bool = False) -> str:
        """Format video analysis results as JSON."""
        if not verbose:
            # Non-verbose mode: only video path and main result
            simplified_results = []
            for result in results:
                simplified = {
                    "video_path": result.get("video_path"),
                    "mode": result.get("mode", "description"),
                    "success": result.get("success", False)
                }
                
                if result.get("success"):
                    simplified["analysis"] = result.get("analysis")
                else:
                    simplified["error"] = result.get("error")
                    
                simplified_results.append(simplified)
            results = simplified_results
        
        if pretty:
            return json.dumps(results, indent=2, ensure_ascii=False)
        return json.dumps(results, ensure_ascii=False)
    
    @staticmethod
    def format_video_markdown(results: list[dict[str, Any]], verbose: bool = False) -> str:
        """Format video analysis results as Markdown."""
        if not results:
            return "# Video Analysis Results\n\nNo results found."
        
        md_content = ["# Video Analysis Results\n"]
        if verbose:
            md_content.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            md_content.append(f"**Total Video Files:** {len(results)}\n")
        
        for i, result in enumerate(results, 1):
            md_content.append(f"## Video {i}: {Path(result['video_path']).name}\n")
            md_content.append(f"**Path:** `{result['video_path']}`\n")
            md_content.append(f"**Mode:** {result.get('mode', 'description')}\n")
            
            if verbose and result.get("video_info"):
                video_info = result["video_info"]
                md_content.append(f"**Duration:** {video_info.get('duration_minutes', 0):.1f} minutes\n")
                md_content.append(f"**Format:** {video_info.get('format', 'unknown')}\n")
                md_content.append(f"**Resolution:** {video_info.get('width', 0)}x{video_info.get('height', 0)}\n")
                md_content.append(f"**File Size:** {video_info.get('file_size_mb', 0):.1f} MB\n")
                
            if verbose:
                if result.get("model"):
                    md_content.append(f"**Model:** {result['model']}\n")
                if result.get("prompt"):
                    md_content.append(f"**Prompt:** {result['prompt']}\n")
                if result.get("word_count"):
                    md_content.append(f"**Word Count:** {result['word_count']}\n")
            
            if result["success"]:
                md_content.append("**Analysis:**\n")
                md_content.append(f"{result.get('analysis', 'No analysis available')}\n")
            else:
                md_content.append(f"**Error:** {result.get('error', 'Unknown error')}\n")
            
            md_content.append("---\n")
        
        return "\n".join(md_content)
    
    @staticmethod
    def format_video_text(results: list[dict[str, Any]], verbose: bool = False) -> str:
        """Format video analysis results as plain text."""
        if not results:
            return "Video Analysis Results\n\nNo results found."
        
        text_content = ["Video Analysis Results"]
        text_content.append("=" * 50)
        
        if verbose:
            text_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            text_content.append(f"Total Video Files: {len(results)}")
            text_content.append("")
        
        for i, result in enumerate(results, 1):
            text_content.append(f"Video {i}: {Path(result['video_path']).name}")
            text_content.append(f"Path: {result['video_path']}")
            text_content.append(f"Mode: {result.get('mode', 'description')}")
            
            if verbose and result.get("video_info"):
                video_info = result["video_info"]
                text_content.append(f"Duration: {video_info.get('duration_minutes', 0):.1f} minutes")
                text_content.append(f"Format: {video_info.get('format', 'unknown')}")
                text_content.append(f"Resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
                text_content.append(f"File Size: {video_info.get('file_size_mb', 0):.1f} MB")
                
            if verbose:
                if result.get("model"):
                    text_content.append(f"Model: {result['model']}")
                if result.get("prompt"):
                    text_content.append(f"Prompt: {result['prompt']}")
                if result.get("word_count"):
                    text_content.append(f"Word Count: {result['word_count']}")
            
            text_content.append("")
            
            if result["success"]:
                text_content.append("Analysis:")
                text_content.append(result.get("analysis", "No analysis available"))
            else:
                text_content.append(f"Error: {result.get('error', 'Unknown error')}")
            
            text_content.append("")
            text_content.append("-" * 50)
            text_content.append("")
        
        return "\n".join(text_content)
    
    def format_video_results(self, results: list[dict[str, Any]], format_type: str, verbose: bool = False) -> str:
        """Format video analysis results in the specified format."""
        if format_type == "json":
            return self.format_video_json(results, verbose=verbose)
        elif format_type == "markdown":
            return self.format_video_markdown(results, verbose=verbose)
        elif format_type == "text":
            return self.format_video_text(results, verbose=verbose)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

class ResultProcessor:
    """Processes and aggregates analysis results."""
    
    @staticmethod
    def aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate results and provide summary statistics."""
        if not results:
            return {
                "total_images": 0,
                "successful_analyses": 0,
                "failed_analyses": 0,
                "success_rate": 0.0,
                "models_used": [],
                "errors": []
            }
        
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        
        models_used = list(set(r.get("model", "unknown") for r in results))
        errors = [r.get("error") for r in failed if r.get("error")]
        
        return {
            "total_images": len(results),
            "successful_analyses": len(successful),
            "failed_analyses": len(failed),
            "success_rate": len(successful) / len(results) * 100,
            "models_used": models_used,
            "errors": errors
        }
    
    @staticmethod
    def filter_results(
        results: list[dict[str, Any]], 
        success_only: bool = False,
        model_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """Filter results based on criteria."""
        filtered = results
        
        if success_only:
            filtered = [r for r in filtered if r.get("success", False)]
        
        if model_filter:
            filtered = [r for r in filtered if r.get("model") == model_filter]
        
        return filtered