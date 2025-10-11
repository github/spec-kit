import { ErrorMessage, FieldMessageFactory, Location } from '../base';
import { ValidationChain } from '../chain';
export declare function check(fields?: string | string[], locations?: Location[], message?: FieldMessageFactory | ErrorMessage): ValidationChain;
