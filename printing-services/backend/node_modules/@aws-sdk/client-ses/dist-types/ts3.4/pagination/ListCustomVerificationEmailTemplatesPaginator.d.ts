import { Paginator } from "@smithy/types";
import {
  ListCustomVerificationEmailTemplatesCommandInput,
  ListCustomVerificationEmailTemplatesCommandOutput,
} from "../commands/ListCustomVerificationEmailTemplatesCommand";
import { SESPaginationConfiguration } from "./Interfaces";
export declare const paginateListCustomVerificationEmailTemplates: (
  config: SESPaginationConfiguration,
  input: ListCustomVerificationEmailTemplatesCommandInput,
  ...rest: any[]
) => Paginator<ListCustomVerificationEmailTemplatesCommandOutput>;
