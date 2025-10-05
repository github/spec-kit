import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  VerifyDomainDkimRequest,
  VerifyDomainDkimResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface VerifyDomainDkimCommandInput extends VerifyDomainDkimRequest {}
export interface VerifyDomainDkimCommandOutput
  extends VerifyDomainDkimResponse,
    __MetadataBearer {}
declare const VerifyDomainDkimCommand_base: {
  new (
    input: VerifyDomainDkimCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    VerifyDomainDkimCommandInput,
    VerifyDomainDkimCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: VerifyDomainDkimCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    VerifyDomainDkimCommandInput,
    VerifyDomainDkimCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class VerifyDomainDkimCommand extends VerifyDomainDkimCommand_base {
  protected static __types: {
    api: {
      input: VerifyDomainDkimRequest;
      output: VerifyDomainDkimResponse;
    };
    sdk: {
      input: VerifyDomainDkimCommandInput;
      output: VerifyDomainDkimCommandOutput;
    };
  };
}
