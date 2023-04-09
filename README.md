# Notion to Obsidian Migration Tool

A simple tool which migrates all your notion notes to be obsidian ready.
It performs the following actions:

1. Removes all UUIDs present on file names, and it's references within other files
2. Converts all database properties present in each file into YAML front-matter
3. Move all non-note attachments into a single folder named 'Attachments'
4. Re-organizes all your notes from folder-structure to a single folder (Can be disabled)
5. Create nested tags based on the sub-folder structure extracted from file re-organization from previous step (Can be disabled)
6. Resolve all link references between files

## Disable options

To disable 