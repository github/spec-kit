import { createPaginator } from "@smithy/core";
import { ListCustomVerificationEmailTemplatesCommand, } from "../commands/ListCustomVerificationEmailTemplatesCommand";
import { SESClient } from "../SESClient";
export const paginateListCustomVerificationEmailTemplates = createPaginator(SESClient, ListCustomVerificationEmailTemplatesCommand, "NextToken", "NextToken", "MaxResults");
