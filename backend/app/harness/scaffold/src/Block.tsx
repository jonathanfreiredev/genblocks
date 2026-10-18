/**
 * A stand-in block, replaced on every sandbox run.
 *
 * It exists so the scaffold can be built, linted and rendered by hand while the
 * harness is being worked on. Nothing here ships to a visitor: the sandbox
 * writes the generated block over this file before it runs anything.
 */
export default function SampleBlock() {
  return (
    <section className="bg-neutral-950 px-6 py-24 text-neutral-50">
      <h1 className="mx-auto max-w-3xl text-4xl font-medium tracking-tight">
        The scaffold, rendered.
      </h1>
    </section>
  );
}
