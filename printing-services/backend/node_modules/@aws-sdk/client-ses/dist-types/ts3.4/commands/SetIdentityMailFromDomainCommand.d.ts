import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  SetIdentityMailFromDomainRequest,
  SetIdentityMailFromDomainResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SetIdentityMailFromDomainCommandInput
  extends SetIdentityMailFromDomainRequest {}
export interface SetIdentityMailFromDomainCommandOutput
  extends SetIdentityMailFromDomainResponse,
    __MetadataBearer {}
declare const SetIdentityMailFromDomainCommand_base: {
  new (
    input: SetIdentityMailFromDomainCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityMailFromDomainCommandInput,
    SetIdentityMailFromDomainCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SetIdentityMailFromDomainCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityMailFromDomainCommandInput,
    SetIdentityMailFromDomainCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SetIdentityMailFromDomainCommand extends SetIdentityMailFromDomainCommand_base {
  protected static __types: {
    api: {
      input: SetIdentityMailFromDomainRequest;
      output: {};
    };
    sdk: {
      input: SetIdentityMailFromDomainCommandInput;
      output: SetIdentityMailFromDomainCommandOutput;
    };
  };
}
