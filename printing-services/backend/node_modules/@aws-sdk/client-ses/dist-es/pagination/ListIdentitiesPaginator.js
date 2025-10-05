import { createPaginator } from "@smithy/core";
import { ListIdentitiesCommand, } from "../commands/ListIdentitiesCommand";
import { SESClient } from "../SESClient";
export const paginateListIdentities = createPaginator(SESClient, ListIdentitiesCommand, "NextToken", "NextToken", "MaxItems");
