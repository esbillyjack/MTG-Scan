# Future Improvements: AI Refusal Handling

This file outlines the plan to implement a Retry button and alternative AI provider for handling AI refusals in the Magic Card Scanner app.

## Overall Architecture Changes
- **For #4 (Retry with Delay)**: Add a button in the scan review dialog that triggers a re-process of the scan. Include a 5-10 second delay to avoid rate limits. This will call the existing `/scan/{scan_id}/process` endpoint again.
- **For #5 (Alternative AI Provider)**: Integrate Anthropic's Claude (as a backup to OpenAI) since it's vision-capable and has similar capabilities. If OpenAI refuses (detected by response text), automatically fall back to Claude. This requires a `CLAUDE_API_KEY` env variable.
- **Detection Logic**: In `ai_processor.py`, check for refusal phrases (e.g., "unable to identify") and trigger the fallback or mark for retry.
- **UI Integration**: Update the review dialog to show the Retry button only if a refusal occurred.
- **Error Handling**: Log fallbacks and add UI feedback (e.g., "Switching to backup AI...").

## Backend Changes
- **Update `ai_processor.py`**:
  - Add Claude integration as a fallback method.
  - Detect refusals and auto-retry once with Claude.
  - For manual retries, the endpoint will handle re-calling the processor.

- **Update `app.py`**:
  - Modify the `/scan/{scan_id}/process` endpoint to support optional "retry" mode (with delay).

## Frontend Changes
- **Update `script.js`**:
  - In the scan results display, add a "Retry Scan" button if refusal detected.
  - Call the process endpoint with a retry flag.

- **Update `styles.css`**:
  - Style the new button.

## Testing
- Start the server.
- Simulate a refused scan and test retry/fallback.
- Verify in logs and UI.

## Environment Setup
- Add `CLAUDE_API_KEY` to your `.env` file (get one from Anthropic's API dashboard).
- Install `anthropic` library via `pip install anthropic` (already added to `requirements.txt`).

This plan can be implemented after other changes. Refer back here when ready. 