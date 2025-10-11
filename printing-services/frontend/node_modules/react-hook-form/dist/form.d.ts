import React from 'react';
import type { FieldValues, FormProps } from './types';
/**
 * Form component to manage submission.
 *
 * @param props - to setup submission detail. {@link FormProps}
 *
 * @returns form component or headless render prop.
 *
 * @example
 * ```tsx
 * function App() {
 *   const { control, formState: { errors } } = useForm();
 *
 *   return (
 *     <Form action="/api" control={control}>
 *       <input {...register("name")} />
 *       <p>{errors?.root?.server && 'Server error'}</p>
 *       <button>Submit</button>
 *     </Form>
 *   );
 * }
 * ```
 */
declare function Form<TFieldValues extends FieldValues, TTransformedValues = TFieldValues>(props: FormProps<TFieldValues, TTransformedValues>): React.JSX.Element;
export { Form };
//# sourceMappingURL=form.d.ts.map