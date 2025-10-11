import { Paginator } from "@smithy/types";
import {
  ListIdentitiesCommandInput,
  ListIdentitiesCommandOutput,
} from "../commands/ListIdentitiesCommand";
import { SESPaginationConfiguration } from "./Interfaces";
export declare const paginateListIdentities: (
  config: SESPaginationConfiguration,
  input: ListIdentitiesCommandInput,
  ...rest: any[]
) => Paginator<ListIdentitiesCommandOutput>;
