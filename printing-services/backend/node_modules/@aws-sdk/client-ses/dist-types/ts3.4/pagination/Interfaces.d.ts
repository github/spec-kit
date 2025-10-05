import { PaginationConfiguration } from "@smithy/types";
import { SESClient } from "../SESClient";
export interface SESPaginationConfiguration extends PaginationConfiguration {
  client: SESClient;
}
