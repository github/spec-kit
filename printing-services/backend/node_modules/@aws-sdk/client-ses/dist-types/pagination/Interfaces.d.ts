import { PaginationConfiguration } from "@smithy/types";
import { SESClient } from "../SESClient";
/**
 * @public
 */
export interface SESPaginationConfiguration extends PaginationConfiguration {
    client: SESClient;
}
