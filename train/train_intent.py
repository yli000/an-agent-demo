import os

import argparse

from collections import Counter


import numpy as np

import torch

from torch.utils.data import Dataset, DataLoader

from tqdm import tqdm

from transformers import (

    BertTokenizerFast,

    BertForSequenceClassification,

    get_linear_schedule_with_warmup,

)

from torch.optim import AdamW


class IntentDataset(Dataset):

    def __init__(self, path, tokenizer, max_len):

        if not os.path.exists(path):

            raise FileNotFoundError(f"{path} not found.")


        self.samples = []

        with open(path, "r", encoding="utf-8") as f:

            for line in f:

                line = line.strip()

                if not line or "\t" not in line:

                    continue

                text, label = line.split("\t", 1)

                try:

                    label = int(label)

                except ValueError:

                    continue

                self.samples.append((text, label))


        label_counter = Counter(label for _, label in self.samples)

        print(f"Loaded {len(self.samples)} samples from {path}")

        print(f"Label distribution (top 10): {label_counter.most_common(10)}")


        self.tokenizer = tokenizer

        self.max_len = max_len


    def __len__(self):

        return len(self.samples)


    def __getitem__(self, idx):

        text, label = self.samples[idx]

        encoded = self.tokenizer.encode_plus(

            text,

            add_special_tokens=True,

            max_length=self.max_len,

            padding="max_length",

            truncation=True,

            return_attention_mask=True,

            return_tensors="pt",

        )

        return {

            "input_ids": encoded["input_ids"].squeeze(0),

            "attention_mask": encoded["attention_mask"].squeeze(0),

            "labels": torch.tensor(label, dtype=torch.long),

        }


def calc_topk_accuracy(logits, labels, ks=(1, 5)):

    max_k = max(ks)

    _, pred = logits.topk(max_k, dim=1, largest=True, sorted=True)

    pred = pred.t()

    correct = pred.eq(labels.view(1, -1).expand_as(pred))


    res = {}

    for k in ks:

        correct_k = correct[:k].reshape(-1).float().sum(0, keepdim=True)

        res[k] = (correct_k / labels.size(0)).item()

    return res


def evaluate(model, loader, device):

    model.eval()

    losses, top1, top5 = [], [], []

    with torch.no_grad():

        for batch in loader:

            input_ids = batch["input_ids"].to(device)

            attention_mask = batch["attention_mask"].to(device)

            labels = batch["labels"].to(device)


            outputs = model(

                input_ids=input_ids, attention_mask=attention_mask, labels=labels

            )

            losses.append(outputs.loss.item())

            accs = calc_topk_accuracy(outputs.logits, labels, ks=(1, 5))

            top1.append(accs[1])

            top5.append(accs[5])


    return np.mean(losses), np.mean(top1), np.mean(top5)


def main():

    parser = argparse.ArgumentParser(description="Intent training with HF BERT")

    parser.add_argument(

        "--data_dir",

        default="./data/intent",

        help="Directory containing train/dev/test/class txt files",

    )

    parser.add_argument(

        "--model_path",

        default="./pretrained/bert-base-uncased",

        help="Path to pretrained BERT directory",

    )

    parser.add_argument(

        "--save_dir",

        default="./saved/intent/bert_base_uncased",

        help="Directory to save HF-format model/tokenizer (optional)",

    )

    parser.add_argument(

        "--ckpt_path",

        default="./saved/intent/bert.ckpt",

        help="Path to save state_dict checkpoint for legacy inference",

    )

    parser.add_argument("--max_len", type=int, default=64)

    parser.add_argument("--batch_size", type=int, default=32)

    parser.add_argument("--epochs", type=int, default=5)

    parser.add_argument("--lr", type=float, default=2e-5)

    parser.add_argument("--weight_decay", type=float, default=0.01)

    args = parser.parse_args()


    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


    class_path = os.path.join(args.data_dir, "class.txt")

    if not os.path.exists(class_path):

        raise FileNotFoundError(f"{class_path} not found.")

    with open(class_path, "r", encoding="utf-8") as f:

        num_labels = len([line for line in f if line.strip()])

    print(f"Detected {num_labels} intent classes.")


    tokenizer = BertTokenizerFast.from_pretrained(args.model_path)


    train_dataset = IntentDataset(

        os.path.join(args.data_dir, "train.txt"), tokenizer, args.max_len

    )

    dev_dataset = IntentDataset(

        os.path.join(args.data_dir, "dev.txt"), tokenizer, args.max_len

    )


    train_loader = DataLoader(

        train_dataset, batch_size=args.batch_size, shuffle=True

    )

    dev_loader = DataLoader(dev_dataset, batch_size=args.batch_size)


    model = BertForSequenceClassification.from_pretrained(

        args.model_path, num_labels=num_labels

    )

    model.to(device)


    optimizer = AdamW(

        model.parameters(), lr=args.lr, weight_decay=args.weight_decay

    )

    total_steps = len(train_loader) * args.epochs

    scheduler = get_linear_schedule_with_warmup(

        optimizer, num_warmup_steps=0, num_training_steps=total_steps

    )


    best_val_acc = 0.0

    os.makedirs(os.path.dirname(args.ckpt_path), exist_ok=True)


    for epoch in range(1, args.epochs + 1):

        print(f"\nEpoch {epoch}/{args.epochs}")

        model.train()

        train_losses = []

        for batch in tqdm(train_loader, desc="Training"):

            input_ids = batch["input_ids"].to(device)

            attention_mask = batch["attention_mask"].to(device)

            labels = batch["labels"].to(device)


            outputs = model(

                input_ids=input_ids,

                attention_mask=attention_mask,

                labels=labels,

            )

            loss = outputs.loss

            train_losses.append(loss.item())


            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

            optimizer.step()

            scheduler.step()

            optimizer.zero_grad()


        val_loss, val_top1, val_top5 = evaluate(model, dev_loader, device)

        print(

            f"Train Loss: {np.mean(train_losses):.4f} | "

            f"Val Loss: {val_loss:.4f} | "

            f"Val Top1: {val_top1:.4f} | Val Top5: {val_top5:.4f}"

        )


        if val_top1 > best_val_acc:

            best_val_acc = val_top1

            if args.save_dir:

                os.makedirs(args.save_dir, exist_ok=True)

                model.save_pretrained(args.save_dir)

                tokenizer.save_pretrained(args.save_dir)

                print(f"=> Saved HF model/tokenizer to {args.save_dir}")

            torch.save(model.state_dict(), args.ckpt_path)

            print(f"=> Saved state_dict checkpoint to {args.ckpt_path}")


    print(f"\nTraining complete. Best Val Top1 Accuracy: {best_val_acc:.4f}")


if __name__ == "__main__":

    main()
