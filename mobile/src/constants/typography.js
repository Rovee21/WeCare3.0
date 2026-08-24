// Centralized font-size scaling for the participant-facing app. WECARE's participant
// base skews older, so all reading text is scaled up from the original design sizes for
// accessibility. Wrapping every `fontSize` in `scaleFont(oldValue)` (rather than hand-typing
// new literals) means the whole app's text size can be re-tuned later by adjusting the
// bands below in one place, instead of another full find-and-replace pass.
//
// Growth rate varies by band on purpose (per stakeholder guidance, not a flat multiplier):
//   - small/caption text grows only modestly, so it stays clearly smaller than body text
//   - body text and most headings get the full ~15-20% bump
//   - large display/title text grows proportionally but a bit more gently in percentage
//     terms, since the absolute pixel jump is already large
//   - values above 32 are left unscaled: at that size a `fontSize` is virtually always a
//     decorative icon-style glyph (an emoji standing in for an icon, a giant checkmark,
//     etc.) rather than text someone is reading, so accessibility scaling doesn't apply,
//     and blowing them up further risks breaking fixed-size circles/buttons they sit in.
export function scaleFont(px) {
  if (px <= 13) return Math.round(px * 1.08);
  if (px <= 22) return Math.round(px * 1.18);
  if (px <= 32) return Math.round(px * 1.12);
  return px;
}
