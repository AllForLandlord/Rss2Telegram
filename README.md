<img align="right" alt="RSS Logo" width="30%" height="auto" src="https://rss.com/blog/wp-content/uploads/2019/10/social_style_3_rss-512-1.png">

# Rss2Telegram

自动将 RSS 订阅内容发送给 Telegram 用户、频道或群组。

[更多说明和使用示例](https://blog.gabrf.com/posts/Rss2Telegram/)。

## 参与项目

欢迎在 [Discussions](https://github.com/GabrielRF/Rss2Telegram/discussions) 中参与项目讨论。

也欢迎提交 Issue。

## 配置

在仓库的 `Secrets` 中设置以下变量：

`BOT_TOKEN`：用于发送消息的机器人令牌（[@BotFather](https://t.me/BotFather)）。

在仓库的 `Variables` 中设置以下变量：

`DESTINATION`：消息接收目标，多个目标用逗号分隔（`@目标` 或 ID）。也可以不设置此变量，改为创建 `DESTINATION.txt` 文件并填写目标。

`URL`：RSS 订阅地址，每行填写一个。也可以不设置此变量，改为创建 `URL.txt` 文件并填写地址。

`PARAMETERS`：（可选）追加到链接末尾的参数。

`MESSAGE_TEMPLATE`：（可选）消息模板。默认值：`<b>{TITLE}</b>`（[可用变量](#变量选项)）。

`BUTTON_TEXT`：（可选）链接按钮的文字，建议使用 `{SITE_NAME}`。未设置时不发送按钮（[可用变量](#变量选项)）。

`EMOJIS`：（可选）用逗号分隔的表情符号，可用于消息或按钮。

`TOPIC`：（可选）消息发送到的话题 ID。启用了话题功能的群组需要设置此项。[如何获取话题 ID](#话题-id)

`TELEGRAPH_TOKEN`：（可选）Telegraph 访问令牌。[如何获取 Telegraph 令牌](#telegraph-令牌)

`HIDE_BUTTON`：（可选）设置后隐藏消息按钮，从而允许使用 `快速浏览`。

### 变量选项

`{SITE_NAME}`：网站名称。

`{TITLE}`：文章标题。

`{SUMMARY}`：文章摘要。

`{LINK}`：文章链接。

`{EMOJI}`：从列表中随机选取的表情符号。

## 过滤规则

默认会发送 RSS 订阅中的所有条目。若要过滤内容，请创建 `RULES.txt` 文件并添加规则。规则将按顺序执行。

> 规则中的匹配词不区分大小写。

`ACCEPT:ALL`：发送所有消息。

`DROP:ALL`：不发送任何消息。

`ACCEPT:词语`：消息中包含该词语时发送。

`DROP:词语`：消息中包含该词语时不发送。

### 过滤规则示例

1. 发送所有消息，但不发送包含 `政治` 的消息：

```
ACCEPT:ALL
DROP:Política
```

2. 不发送任何消息，但发送包含 `足球` 或 `排球` 的消息：

```
DROP:ALL
ACCEPT:futebol
ACCEPT:vôlei
```

## 使用方法

Fork 此仓库，设置变量，然后点击“*Enable workflow*”启用工作流即可。

![Enable Workflow](https://user-images.githubusercontent.com/7331540/178158090-bf774cae-071b-4ac2-ab03-9c5c1132b79e.png)

工作流会按照 [cron.yml](.github/workflows/cron.yml) 中的设置每小时检查一次更新。

## 话题 ID

如果群组启用了话题功能，需要使用 `TOPIC` 变量指定消息发送到哪个话题。最简单的获取方式是复制话题中一条消息的链接；链接中的倒数第二个数字就是话题 ID。

例如，话题消息链接为 `https://t.me/c/987654321/123/4567` 时，话题 ID 是 `123`，应将其填入该变量。

## Telegraph 令牌

> 注意：设置 <i>TELEGRAPH_TOKEN</i> 后，文章消息将不包含按钮或图片，因为这两者与“快速浏览”功能不兼容。

要创建 Telegraph 访问令牌，并为网站生成<i>快速浏览</i>页面，请访问：

```
https://api.telegra.ph/createAccount?short_name=<SHORT_NAME>&author_name=<AUTHOR_NAME>
```

* `SHORT_NAME`：名称缩写。

* `AUTHOR_NAME`：名称。

网站返回的结果类似如下：

```
{
  "ok": true,
  "result": {
    "short_name": "NOME",
    "author_name": "NOME",
    "author_url": "",
    "access_token": "abcdefghijklmnopqrtuvxz123456789",
    "auth_url": "https://edit.telegra.ph/auth/123456789012345678901234567890"
  }
}
```

将 `access_token` 的值填入 `TELEGRAPH_TOKEN` 变量。
