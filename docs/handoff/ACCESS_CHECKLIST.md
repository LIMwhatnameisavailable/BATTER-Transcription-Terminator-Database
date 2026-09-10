# BTED 权限交接清单

本文件只记录资源、所需权限和验证方式。禁止填写 token、密码、SSH 私钥、恢复码、数据库 URL
或带凭据链接。维护者使用自己的账号和最小权限凭据，不转发现有个人 token。

## 1. 交接前需要用户提供

- 同事的 GitHub 用户名；
- 同事的 Cloudflare 账号邮箱或团队成员标识；
- 同事的 Hugging Face 用户名；
- 是否需要发布权限，还是先只给只读/开发权限；
- 双方约定的权限复核和旧凭据撤销日期。

## 2. GitHub

| 项目 | 当前资源 | 建议权限 | 验证 |
|---|---|---|---|
| 交接仓库 | `seu-yolo/BATTER-Transcription-Terminator-Database` | Write | 能 fetch/push 自己的测试分支 |
| 交接分支 | `handoff/bted-maintainer-2026-09` | Write | 能 clone、switch 并读取全部提交 |
| 上游仓库 | `LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database` | 按团队制度 | 能读取 issue/PR；没有授权时不得直接 push |
| Actions/Pages | 对应仓库设置 | Read；负责发布时再给 Write | 能查看历史 run，不触发发布 |

邀请后，同事使用自己的 SSH key 或 GitHub token。不要复制原维护者的 credential helper 内容。
历史 worktree/branch 状态记录在 `docs/HANDOFF.md`；交接过程不自动删除、合并或 force-push。

## 3. Cloudflare

| 资源 | 当前值 | 最小能力 |
|---|---|---|
| Worker | `bted-catalogue-v03-preview` | 读取配置和 deployments |
| D1 | `bted-catalogue-v03-preview` | 只读查询；负责发布时才授予写入 |
| D1 binding | `BTED_DB` | 查看 Worker binding |
| Static Assets | 仓库 `site/` | 查看已部署版本 |

先验证：

```bash
CI=1 npx wrangler whoami
npx wrangler deployments list --config prototype/accession-range/wrangler.jsonc
npx wrangler d1 execute bted-catalogue-v03-preview --remote \
  --command "SELECT release_version, status FROM releases;" \
  --config prototype/accession-range/wrangler.jsonc
```

最后一条必须保持只读 SELECT。没有明确发布授权时，不运行 deploy，不执行
DROP/TRUNCATE/DELETE/UPDATE/INSERT，不创建新数据库。

优先通过 Cloudflare 成员角色授权；若账号方案不支持所需粒度，再由用户决定是否创建新的 scoped
API token。任何 token 都只保存在本机安全存储或 CI secret，不进入 Git、聊天或日志。

## 4. Hugging Face

| 资源 | 当前值 | 最小能力 |
|---|---|---|
| Dataset | `seu-yolo/BTED-v0.3-assets` | Read；负责资产发布时才需要 Write |
| 固定 revision | `463cfc8bd582a5ed9d2c426822148c3f1e56c4d0` | 必须能读取 |
| public objects | 208，196,667,360 bytes | HEAD 与 Range 读取 |

同事使用自己的 HF 账号和 token，通过仓库 collaborator/organization 权限接入。若个人 dataset
无法安全授予独立维护权，不共享所有者 token；暂停写权限交接，由用户决定是否迁移到组织名下。
固定 revision 未变化时无需重新上传。

## 5. 公共科研来源

NCBI/GEO/SRA/ENA、PubMed、Zenodo、论文 DOI 和公开 GitHub 仓库通常不需要项目凭据。交接的是
来源链接、版本、许可与引用规则，不是网站登录账号。出版商补充材料的再分发条件仍需逐来源遵守。

## 6. 当前不需要交接的服务

- MySQL：项目未使用。
- Render/Neon/Vercel：不是当前部署依赖。
- PostgreSQL/FastAPI/Next.js：保留为 future/alternative，没有已上线数据库账号可交接。
- 本地 `/private/tmp`、`.wrangler/` cache 和终端日志：可再生成，不属于交接资产。

## 7. 双方验收

- [ ] 同事可使用自己的身份 clone/fetch/push 个人测试分支。
- [ ] 同事可查看 Worker deployments 和执行只读 D1 SELECT。
- [ ] 同事可读取固定 HF revision 和代表性对象的 HEAD/Range。
- [ ] 同事确认没有收到原维护者 token、密码、SSH 私钥或 2FA 恢复码。
- [ ] 同事按 `DEMO_AND_ACCEPTANCE.md` 完成本地与线上核验。
- [ ] 用户确认是否保留原维护者发布权限；仅在真正完成所有权转移后撤销旧权限。
