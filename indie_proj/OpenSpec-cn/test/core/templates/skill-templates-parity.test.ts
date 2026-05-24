import { createHash } from 'node:crypto';
import { describe, expect, it } from 'vitest';

import {
  type SkillTemplate,
  getApplyChangeSkillTemplate,
  getArchiveChangeSkillTemplate,
  getBulkArchiveChangeSkillTemplate,
  getContinueChangeSkillTemplate,
  getExploreSkillTemplate,
  getFeedbackSkillTemplate,
  getFfChangeSkillTemplate,
  getNewChangeSkillTemplate,
  getOnboardSkillTemplate,
  getOpsxApplyCommandTemplate,
  getOpsxArchiveCommandTemplate,
  getOpsxBulkArchiveCommandTemplate,
  getOpsxContinueCommandTemplate,
  getOpsxExploreCommandTemplate,
  getOpsxFfCommandTemplate,
  getOpsxNewCommandTemplate,
  getOpsxOnboardCommandTemplate,
  getOpsxSyncCommandTemplate,
  getOpsxProposeCommandTemplate,
  getOpsxProposeSkillTemplate,
  getOpsxVerifyCommandTemplate,
  getSyncSpecsSkillTemplate,
  getVerifyChangeSkillTemplate,
} from '../../../src/core/templates/skill-templates.js';
import { generateSkillContent } from '../../../src/core/shared/skill-generation.js';

const EXPECTED_FUNCTION_HASHES: Record<string, string> = {
  getExploreSkillTemplate: '82d2299171c86e531bfe9253399873c90d646f1e38506e15ea7d42176f49aff0',
  getNewChangeSkillTemplate: 'a745f8794b4717a201e001e99ef8ec67196e1057ecb3737a6963f5a5a9f4ba43',
  getContinueChangeSkillTemplate: 'fb04aa237e07898fff39481d5b544f0d9dae4dc5a83c75673e3bb2381e5a4f40',
  getApplyChangeSkillTemplate: 'b1cf688fb2d5531c5edb46c3ea86351934408d7ead874040d9b888aaf224ea2e',
  getFfChangeSkillTemplate: 'fe29d7df3a0c55f1f557452338568d57fd719be89cdff7f382235046bb87c4fa',
  getSyncSpecsSkillTemplate: 'f6b8ad7ab0b6a52e22d372e72456a74b804bcb4418bfea25a9db40448a7d5639',
  getOnboardSkillTemplate: 'b7af2de97b5fd5afce5117b06bc81a8feebdd1bb3fa3c760cfb1debe24100705',
  getOpsxExploreCommandTemplate: '6e76e88b1c37c87c53d25abceb349068092e33d885a18617f4045f1ddc2004f7',
  getOpsxNewCommandTemplate: '30025e2d64114b8a4200fa4fd4d1f4c6830debdee797e57abf7eced0fe1e5756',
  getOpsxContinueCommandTemplate: '1eb4aeefed580ff62fc0a4c88a547af07712aec9b18c7d8d840d674d738ab411',
  getOpsxApplyCommandTemplate: '5d2d1bec50c6c034da949dfa5abe63f7c2b92607aa6cadb78a2e1678b38ce0e7',
  getOpsxFfCommandTemplate: 'ab0169144d641391ab6e4f99e06add8bb76d5df06ddac563d64bbff1c709a4b9',
  getArchiveChangeSkillTemplate: 'b14b5d54f1a84c4239a9678ac3b99f6372c8344320364f5524f4a81527021446',
  getBulkArchiveChangeSkillTemplate: '7b8c85795a64190dd7e606ec1c25b78e59a8f87643537e6eba210b3c9ab432ff',
  getOpsxSyncCommandTemplate: '097d192c440b5ee6998f628c33e4acc4a4bf0e9fe09ea65fa8e88952fb31272b',
  getVerifyChangeSkillTemplate: '9144c160e38c5802449e39e46d1c49e04fbfc1c5217f322feaf7b024775be9a7',
  getOpsxArchiveCommandTemplate: '0aa68cc2e4ae0559f0c98bf8224490c516691780b5e9933f4f8310418a4e1b97',
  getOpsxOnboardCommandTemplate: 'c759a5b5751b77e47c4f53c22938189a79c54a0ce647df3eda82c59b33754c87',
  getOpsxBulkArchiveCommandTemplate: '6fc1eacbe475036088b94120769be59e4e98fd1980cb91bf7c98235331f5db4d',
  getOpsxVerifyCommandTemplate: 'c958655ba5361104629b2209a5ecba82108af85e20458c2b7c8bb1efc8f75bc1',
  getOpsxProposeSkillTemplate: '86713fde6dbaa6be1f996d1c3505e361b9be4e757c946f727dc8958a8a61bed2',
  getOpsxProposeCommandTemplate: 'af4c1de01d21d81806ebd7e745653a0017aa99ed154b1d7ee03c915e77aa505b',
  getFeedbackSkillTemplate: 'a2ee906458fa2cad42096fe0ec40000f3acfd5534d91bd48079ff3a19af914e3',
};

const EXPECTED_GENERATED_SKILL_CONTENT_HASHES: Record<string, string> = {
  'openspec-explore': 'd4b9e68b1d0b632eb3507662047e2deee6a819c91e2a7b46c384541c9f4bf0c0',
  'openspec-new-change': 'ab9020a8468ec7186f2bf7f9b7017b4a2eb4ea861eb28d077f2d582dd8e16ff8',
  'openspec-continue-change': 'aa45e0220ac7cd9b56b6eb2762c7d3c7038e1ffba843304d05ef2d64a0a419ba',
  'openspec-apply-change': '6e4ed9745924712b869d743cc5f1952be3a0036da537596c43b8baefa88dff62',
  'openspec-ff-change': '4f781bc02e5c53a9978aec3ad07ec0bf90eb571e13916034258b4639e618e8cd',
  'openspec-sync-specs': '21386f3b4bf05e0e451a9938e54d2162ff82d5324fabb947d68a2071254cb445',
  'openspec-archive-change': '2c407d800b1c6b50acc4d5fadbd871a7f55719b401e162876e686e5e3175423b',
  'openspec-bulk-archive-change': '4edc5c8f24005fe5ec19d71695184908f1a6239cd89021cf276f100bfc0742b0',
  'openspec-verify-change': '48e9c729e2b67c938418a6812ec12a8f201ec168bb10dbb241a00695a2b02fa2',
  'openspec-onboard': '0e41d9b7c171b6ab784a424e4965afbd1b26d4c71c19d911bec42a7d48192b35',
  'openspec-propose': '4278ce86cf17958e1bed5877e6418d893f4923f318684dd90b3142309f248de4',
};

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(',')}]`;
  }

  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => `${JSON.stringify(key)}:${stableStringify(item)}`);

    return `{${entries.join(',')}}`;
  }

  return JSON.stringify(value);
}

function hash(value: string): string {
  return createHash('sha256').update(value).digest('hex');
}

describe('skill templates split parity', () => {
  it('preserves all template function payloads exactly', () => {
    const functionFactories: Record<string, () => unknown> = {
      getExploreSkillTemplate,
      getNewChangeSkillTemplate,
      getContinueChangeSkillTemplate,
      getApplyChangeSkillTemplate,
      getFfChangeSkillTemplate,
      getSyncSpecsSkillTemplate,
      getOnboardSkillTemplate,
      getOpsxExploreCommandTemplate,
      getOpsxNewCommandTemplate,
      getOpsxContinueCommandTemplate,
      getOpsxApplyCommandTemplate,
      getOpsxFfCommandTemplate,
      getArchiveChangeSkillTemplate,
      getBulkArchiveChangeSkillTemplate,
      getOpsxSyncCommandTemplate,
      getVerifyChangeSkillTemplate,
      getOpsxArchiveCommandTemplate,
      getOpsxOnboardCommandTemplate,
      getOpsxBulkArchiveCommandTemplate,
      getOpsxVerifyCommandTemplate,
      getOpsxProposeSkillTemplate,
      getOpsxProposeCommandTemplate,
      getFeedbackSkillTemplate,
    };

    const actualHashes = Object.fromEntries(
      Object.entries(functionFactories).map(([name, fn]) => [name, hash(stableStringify(fn()))])
    );

    expect(actualHashes).toEqual(EXPECTED_FUNCTION_HASHES);
  });

  it('preserves generated skill file content exactly', () => {
    // Intentionally excludes getFeedbackSkillTemplate: skillFactories only models templates
    // deployed via generateSkillContent, while feedback is covered in function payload parity.
    const skillFactories: Array<[string, () => SkillTemplate]> = [
      ['openspec-explore', getExploreSkillTemplate],
      ['openspec-new-change', getNewChangeSkillTemplate],
      ['openspec-continue-change', getContinueChangeSkillTemplate],
      ['openspec-apply-change', getApplyChangeSkillTemplate],
      ['openspec-ff-change', getFfChangeSkillTemplate],
      ['openspec-sync-specs', getSyncSpecsSkillTemplate],
      ['openspec-archive-change', getArchiveChangeSkillTemplate],
      ['openspec-bulk-archive-change', getBulkArchiveChangeSkillTemplate],
      ['openspec-verify-change', getVerifyChangeSkillTemplate],
      ['openspec-onboard', getOnboardSkillTemplate],
      ['openspec-propose', getOpsxProposeSkillTemplate],
    ];

    const actualHashes = Object.fromEntries(
      skillFactories.map(([dirName, createTemplate]) => [
        dirName,
        hash(generateSkillContent(createTemplate(), 'PARITY-BASELINE')),
      ])
    );

    expect(actualHashes).toEqual(EXPECTED_GENERATED_SKILL_CONTENT_HASHES);
  });

  it('documents Redmine issue driven propose inputs', () => {
    const skill = getOpsxProposeSkillTemplate().instructions;
    const command = getOpsxProposeCommandTemplate().content;

    for (const content of [skill, command]) {
      expect(content).toContain('Redmine 单号引用');
      expect(content).toContain('`redmine:#12`');
      expect(content).toContain('普通 `#12` 视为用户描述的一部分');
      expect(content).toContain('red-cli issue view <issue-id> --json');
      expect(content).toContain('`issue.subject`');
      expect(content).toContain('`redmine-<issue-id>-<subject-kebab>`');
      expect(content).toContain('`redmine-12-add-login-audit`');
      expect(content).toContain('用户在单号后追加的额外描述');
    }
  });

  it('documents Redmine status sync when applying changes', () => {
    const skill = getApplyChangeSkillTemplate().instructions;
    const command = getOpsxApplyCommandTemplate().content;

    for (const content of [skill, command]) {
      expect(content).toContain('redmine.issueId');
      expect(content).toContain('red-cli issue edit <issue-id> --status "Applying"');
      expect(content).toContain('开始第一个实现任务前');
    }
  });

  it('documents Redmine archive notes and post-archive status sync', () => {
    const skill = getArchiveChangeSkillTemplate().instructions;
    const command = getOpsxArchiveCommandTemplate().content;

    for (const content of [skill, command]) {
      expect(content).toContain('Redmine 归档说明');
      expect(content).toContain('git diff --stat');
      expect(content).toContain('red-cli issue note <issue-id> --message-file <note-file>');
      expect(content).toContain('red-cli issue edit <issue-id> --status "Code Review"');
      expect(content).toContain('QA 检查建议');
    }
  });
});
