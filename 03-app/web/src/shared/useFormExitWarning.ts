import { useEffect } from 'react';
export function useFormExitWarning(form: { isFieldsTouched: () => boolean }, enabled = true) {
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (enabled && form.isFieldsTouched()) { event.preventDefault(); event.returnValue = ''; }
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [form, enabled]);
}
