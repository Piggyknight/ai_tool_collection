package issue

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/MrJeffLarry/redmine-cli/internal/api"
	"github.com/MrJeffLarry/redmine-cli/internal/config"
	"github.com/MrJeffLarry/redmine-cli/internal/editor"
	"github.com/MrJeffLarry/redmine-cli/internal/print"
	"github.com/spf13/cobra"
)

// cmdIssueNoteRun is the extracted implementation for the note command's run behavior.
func cmdIssueNoteRun(r *config.Red_t, cmd *cobra.Command, args []string) {
	id := cmd.Flags().Arg(0)
	if len(id) == 0 {
		fmt.Println("Please specify the issue id: note [id]")
		return
	}

	msg, _ := cmd.Flags().GetString("message")
	msgFile, _ := cmd.Flags().GetString("message-file")
	if msg != "" && msgFile != "" {
		fmt.Println("Please use either --message or --message-file, not both")
		return
	}

	if msgFile != "" {
		body, err := os.ReadFile(msgFile)
		if err != nil {
			print.Error("Could not read message file: %s", err.Error())
			return
		}
		msg = string(body)
	}

	if msg == "" {
		// open editor for message
		msg = editor.StartEdit(r.Config.Editor, "")
	}

	if msg == "" {
		fmt.Println("No message provided, aborting")
		return
	}

	// build payload and include private_notes if requested
	issueFields := map[string]interface{}{
		"notes": msg,
	}
	if priv, _ := cmd.Flags().GetBool("private"); priv {
		issueFields["private_notes"] = true
	}

	payload := map[string]map[string]interface{}{
		"issue": issueFields,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		print.Debug(r, err.Error())
		print.Error("Could not compose note payload")
		return
	}

	path := "/issues/" + id + ".json"
	res, status, err := api.ClientPUT(r, path, body)
	if err != nil {
		print.Error("StatusCode %d, %s", status, err.Error())
		return
	}

	print.Debug(r, "%d %s", status, string(res))

	if err := api.StatusCode(status); err != nil {
		print.Error("%s", err.Error())
		return
	}

	print.OK("Note added to issue %s", id)
}

func cmdIssueNote(r *config.Red_t) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "note [id]",
		Short: "Add a note to an issue",
		Long:  "Add a journal note to an existing issue",
		Run: func(cmd *cobra.Command, args []string) {
			cmdIssueNoteRun(r, cmd, args)
		},
	}

	cmd.Flags().StringP("message", "m", "", "Message to post as a note (if empty opens editor)")
	cmd.Flags().String("message-file", "", "Read note message from a file")
	cmd.Flags().BoolP("private", "p", false, "Post the note as private (private_notes)")
	return cmd
}
