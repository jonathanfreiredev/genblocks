# Motion

Movement is worth having when it explains something: what arrived, what changed,
where a thing came from. It is never worth having as a greeting.

- **What earns it**: a panel that lifts as it opens, an item that enters when it
  is added, a tab indicator that slides because it is the same thing moving, a
  number that counts up to the value it describes, a hint that appears the moment
  somebody needs it.
- **What does not**: everything animating on load, a headline that fades in
  because the page had room, hover states with more than a transition, movement
  that loops with no state behind it, animation standing in for hierarchy.
- **Cheap first**: `transition-*` with a real duration (150–300ms) and `ease-out`
  for state changes; a keyframe in an inline `<style>` for one-shot entrances;
  `motion` when the movement needs a spring, a sequence, an exit, or a layout
  change. If you cannot say what the movement explains, do not ship it.
- **With `motion`**, keep it to what Tailwind cannot do: `<motion.div
  initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>` for an
  entrance, `AnimatePresence` for something leaving, and `layout` when an element
  moves because the layout did.
- **Respect the setting**: `const reduce = useReducedMotion()` from `motion/react`,
  or Tailwind's `motion-reduce:` variant, and make the outcome the same without
  movement — the content still arrives, it just arrives. This is measured: the
  sandbox reloads with `prefers-reduced-motion: reduce` and no entrance longer than
  ~200ms, and nothing repeating, may still be running.
- **Never block**: no animation may hide content, delay reading, hijack scroll, or
  move a control somebody is aiming at. Entrances are short and they end.
- **The render waits for animations to settle before it is photographed**, and a
  block whose content only exists mid-animation is scored as what it looks like at
  rest: empty. If something has to be seen, it has to be there without moving.
