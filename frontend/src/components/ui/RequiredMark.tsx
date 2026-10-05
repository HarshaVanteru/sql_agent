/**
 * The asterisk on a required field's label.
 *
 * aria-hidden with a text alternative beside it: a screen reader announces
 * "required" from the input's own `required` attribute, and would otherwise
 * read the asterisk as "star" on top of it.
 */
export function RequiredMark() {
  return (
    <>
      <span aria-hidden="true" className="ml-0.5 text-danger">
        *
      </span>
      <span className="sr-only"> (required)</span>
    </>
  );
}
