"""Data export module."""

import os
from typing import Any, Dict, Optional

from .config import settings


class DataExporter:
    """Handles README file generation."""

    def update_readme(self, content: Optional[Dict[str, str]]) -> bool:
        """Update README files with generated content in multiple languages."""
        if not content:
            print("⚠ No content to update")
            return False

        output_dir = settings.output_dir
        if output_dir and output_dir != ".":
            os.makedirs(output_dir, exist_ok=True)

        # Save Portuguese version
        pt_filename = os.path.join(output_dir, "README.pt-br.md")
        with open(pt_filename, "w", encoding="utf-8") as f:
            f.write(content.get("pt-br", ""))
        print(f"✓ {pt_filename} updated!")

        # Save English version
        en_filename = os.path.join(output_dir, "README.en.md")
        with open(en_filename, "w", encoding="utf-8") as f:
            f.write(content.get("en", ""))
        print(f"✓ {en_filename} updated!")

        # Save main README (Portuguese version as default)
        main_filename = os.path.join(output_dir, settings.readme_filename)
        with open(main_filename, "w", encoding="utf-8") as f:
            f.write(content.get("pt-br", ""))
        print(f"✓ {main_filename} updated!")

        return True
